import asyncio
from datetime import datetime
from uuid import uuid4
from openai import pydantic_function_tool
from time import time
import json
import numpy as np

from app.services.chat import ChatService
from app.services.db import add_chunks_to_vector_db, get_chat_messages, search_vector_db
from app.assistants.tools import QueryKnowledgeBaseTool
from app.assistants.prompts import INITIAL_PROMPT_TEMPLATE, MAIN_SYSTEM_PROMPT, RAG_SYSTEM_PROMPT, THEME_DICTS
from app.utils import chat_stream, get_embedding

class RAGAssistant:
    def __init__(self, chat_id, rdb, chat_service: ChatService, history_size=4, max_tool_calls=3):
        self.chat_id = chat_id
        self.rdb = rdb
        self.chat_service = chat_service
        self.main_system_message = {'role': 'system', 'content': MAIN_SYSTEM_PROMPT}
        self.rag_system_message = {'role': 'system', 'content': RAG_SYSTEM_PROMPT}
        self.tools_schema = [pydantic_function_tool(QueryKnowledgeBaseTool)]
        self.history_size = history_size
        self.max_tool_calls = max_tool_calls

    async def _generate_chat_response(self, system_message, chat_messages, send_func, **kwargs):
        messages = [system_message, *chat_messages]
        accumulated_content = ""
        buffered_chunks: list[dict] = []
        
        async with chat_stream(messages=messages, **kwargs) as stream:
            async for event in stream:
                if event.type == 'chunk':
                    chunk = event.chunk.choices[0]
                    content = chunk.delta.content or ''
                    reason = chunk.finish_reason or 'no'

                    if content:
                        accumulated_content += content

                    buffered_chunks.append({
                        'type': 'stream',
                        'chunk': content,
                        'role': 'assistant',
                        'finish_reason': reason
                    })

            final_completion = await stream.get_final_completion()
            assistant_message = final_completion.choices[0].message

        validated = False    
        if accumulated_content.strip():
            validated = await self._validate_and_store_response(accumulated_content, chat_messages)

        if not validated:
            error_payload = {
                'type': 'stream',
                'chunk': "I'm not sure about that. Can you please rephrase or provide more context?",
                'finish_reason': 'stop'
            }
            await send_func(error_payload)
            assistant_message.message = error_payload
            assistant_message.error = "error"

            return assistant_message
        
        for payload in buffered_chunks:
            await send_func(payload)

        return assistant_message
        
    async def _handle_tool_calls(self, tool_calls, chat_messages, send_func):
        for tool_call in tool_calls[:self.max_tool_calls]:
            kb_tool = tool_call.function.parsed_arguments
            kb_result = await kb_tool(self.rdb)
            chat_messages.append({
                'role': 'tool',
                'tool_call_id': tool_call.id,
                'content': kb_result
            })
        return await self._generate_chat_response(
            system_message=self.rag_system_message,
            chat_messages=chat_messages,
            send_func=send_func
        )

    async def _validate_and_store_response(self, response_content, chat_messages) -> bool:
        user_question = None
        for msg in reversed(chat_messages):
            if msg['role'] == 'user':
                user_question = msg['content']
                break
        
        if not user_question:
            return False
        
        query_vector = await get_embedding(user_question)
        kb_context = await search_vector_db(self.rdb, query_vector, top_k=3)
        
        is_valid = await self._validate_by_similarity(
            response_content, 
            kb_context
        )
        
        if is_valid:
            await self._store_validated_response(response_content, user_question, kb_context)
            return True
        
        return False
    
    async def _store_validated_response(self, response_content, user_question, kb_context):
        response_vector = await get_embedding(response_content)
        
        chunk = {
            'chunk_id': str(uuid4()),
            'text': response_content,
            'doc_name': f'assistant_response_{self.chat_id}',
            'vector': response_vector,
            'metadata': {
                'type': 'assistant_response',
                'chat_id': self.chat_id,
                'user_question': user_question,
                'timestamp': int(time()),
                'context_sources': [c['doc_name'] for c in kb_context[:2]]
            }
        }

        await add_chunks_to_vector_db(self.rdb, [chunk])
    
    async def _validate_by_similarity(self, response, kb_context) -> bool:
        if not kb_context:
            return False
        
        response_vector = await get_embedding(response)

        similarities = []

        for chunk in kb_context[:3]:
            chunk_vector = await get_embedding(chunk['text'])
            similarity = self._cosine_similarity(response_vector, chunk_vector)
            similarities.append(similarity)

        if max(similarities) < 0.5:
            chat = await self.chat_service.conversation_repo.get_by_id(self.chat_id)
            if not chat or not chat.context_id:
                return False
            
            context = await self.chat_service.context_repo.get_by_id(chat.context_id)
            theme = context.title.lower() if context else 'coffee'
            keywords = THEME_DICTS.get(theme, [])

            return any(kw in response.lower() for kw in keywords)
        
        return True

    def _cosine_similarity(self, vec1, vec2):
        vec1, vec2 = np.array(vec1), np.array(vec2)
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    
    async def run(self, message, send_func, store_user_message: bool = True):
        try:
            chat_messages = await get_chat_messages(self.rdb, self.chat_id, last_n=self.history_size)
            chat = await self.chat_service.conversation_repo.get_by_id(self.chat_id)            
            context = await self.chat_service.context_repo.get_by_id(chat.context_id)
            chat_theme = context.title

            if store_user_message:
                user_db_message = {
                    'role': 'user',
                    'content': message,
                    'created': int(time())
                }
            else:
                message = INITIAL_PROMPT_TEMPLATE.format(theme_title=chat_theme)
                user_db_message = None

            user_message_for_context = {'role': 'user', 'content': message}
            chat_messages.append(user_message_for_context)
            
            assistant_message = await self._generate_chat_response(
                system_message=self.main_system_message,
                chat_messages=chat_messages,
                send_func=send_func,
                tools=self.tools_schema
            )
            
            tool_calls = assistant_message.tool_calls or []

            if tool_calls:
                chat_messages.append(assistant_message)
                assistant_message = await self._handle_tool_calls(tool_calls, chat_messages, send_func)

            assistant_db_message = {
                'role': 'assistant',
                'content': assistant_message.content,
                'tool_calls': [
                    {'name': tc.function.name, 'arguments': tc.function.arguments} for tc in tool_calls
                ],
                'created': int(time())
            }

            messages_to_store = [assistant_db_message]
            if user_db_message:
                messages_to_store.insert(0, user_db_message)

            await self.chat_service.add_chat_messages(self.chat_id, messages_to_store)

        except Exception as e:
            await send_func({'type': 'error', 'message': str(e)})
        finally:
            await send_func({'type': 'done'})