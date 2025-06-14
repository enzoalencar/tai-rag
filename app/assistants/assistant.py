import asyncio
from uuid import uuid4
from openai import pydantic_function_tool
from time import time
import json
from fastapi import Depends
import numpy as np

from app.services.db import add_chunks_to_vector_db, get_chat_messages, search_vector_db
from app.utils.di_container import get_chat_service
from app.assistants.tools import QueryKnowledgeBaseTool
from app.assistants.prompts import MAIN_SYSTEM_PROMPT, RAG_SYSTEM_PROMPT
from app.utils import SSEStream, get_chat_service, chat_stream, get_embedding, get_embeddings

class RAGAssistant:
    def __init__(self, chat_id, rdb, history_size=4, max_tool_calls=3):
        self.chat_id = chat_id
        self.rdb = rdb
        self.chat_service = Depends(get_chat_service)
        self.sse_stream = None
        self.main_system_message = {'role': 'system', 'content': MAIN_SYSTEM_PROMPT}
        self.rag_system_message = {'role': 'system', 'content': RAG_SYSTEM_PROMPT}
        self.tools_schema = [pydantic_function_tool(QueryKnowledgeBaseTool)]
        self.history_size = history_size
        self.max_tool_calls = max_tool_calls

    async def _generate_chat_response(self, system_message, chat_messages, **kwargs):
        messages = [system_message, *chat_messages]
        accumulated_content = ""
        
        async with chat_stream(messages=messages, **kwargs) as stream:
            async for event in stream:
                if event.type == 'chunk':
                    chunk_content = event.chunk.choices[0].delta.content
                    if chunk_content:
                        accumulated_content += chunk_content
                    
                    payload = {
                        'message': chunk_content,
                        'finish_reason': event.chunk.choices[0].finish_reason or 'no'
                    }
                    await self.sse_stream.send(json.dumps(payload))

            final_completion = await stream.get_final_completion()
            assistant_message = final_completion.choices[0].message
            
            if accumulated_content.strip():
                await self._validate_and_store_response(accumulated_content, chat_messages)
            
            return assistant_message
        
    async def _handle_tool_calls(self, tool_calls, chat_messages):
        for tool_call in tool_calls[:self.max_tool_calls]:
            kb_tool = tool_call.function.parsed_arguments
            kb_result = await kb_tool(self.rdb)
            chat_messages.append(
                {'role': 'tool', 'tool_call_id': tool_call.id, 'content': kb_result}
            )
        return await self._generate_chat_response(
            system_message=self.rag_system_message,
            chat_messages=chat_messages,
        )
    
    async def _run_conversation_step(self, message):
        user_db_message = {'role': 'user', 'content': message, 'created': int(time())}
        chat_messages = await get_chat_messages(self.rdb, self.chat_id, last_n=self.history_size)
        chat_messages.append({'role': 'user', 'content': message})
        assistant_message = await self._generate_chat_response(
            system_message=self.main_system_message,
            chat_messages=chat_messages,
            tools=self.tools_schema
        )
        tool_calls = assistant_message.tool_calls or []

        if tool_calls:
            chat_messages.append(assistant_message)
            assistant_message = await self._handle_tool_calls(tool_calls, chat_messages)
        
        assistant_db_message = {
            'role': 'assistant',
            'content': assistant_message.content,
            'tool_calls': [
                {'name': tc.function.name, 'arguments': tc.function.arguments} for tc in tool_calls
            ],
            'created': int(time())
        }
        await self.chat_service.add_chat_messages(self.rdb, self.chat_id, [user_db_message, assistant_db_message])

    async def _handle_conversation_task(self, message):
        try:
            await self._run_conversation_step(message)
        except Exception as e:
            print(f'Error: {str(e)}')
        finally:
            await self.sse_stream.close()

    async def _validate_and_store_response(self, response_content, chat_messages):
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
            user_question, 
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
    
    async def _validate_by_similarity(self, response, question, kb_context):
        # todo :: Implementar validação
        return True

    def _cosine_similarity(self, vec1, vec2):
        vec1, vec2 = np.array(vec1), np.array(vec2)
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

    def run(self, message):
        self.sse_stream = SSEStream()
        asyncio.create_task(self._handle_conversation_task(message))
        return self.sse_stream
