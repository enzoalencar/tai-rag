# tAI - Backend

## Sobre
Para usuários de smartphone, que busquem aprimorar os conhecimentos da língua inglesa, o “tAI” é um aplicativo móvel que gera contextos de conversas do cotidiano de falantes nativos. Ao contrário de alternativas do mercado que exigem esforços que partem do usuário, nosso produto já entrega uma conversa aleatória sem o cliente precisar pensar em assuntos.

## Tecnologias
- Python
- Fast API
- Pydantic
- SQLAlchemy
- Alembic
- Redis Vector DB
- PostgreSQL
- Open AI API

## Princípios SOLID

### Single Responsibility Principle (SRP)
Cada classe tem uma única responsabilidade bem definida. Os repositórios gerenciam apenas operações de dados para entidades específicas, enquanto serviços encapsulam lógica de negócios.

```python
class AgentRepository(AgentRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_model(self, model: str) -> Agent | None:
        query = select(Agent).where(Agent.model == model).limit(1)
        res = await self.session.execute(query)
        return res.first()
```

### Open/Closed Principle (OCP)
O sistema é aberto para extensão mas fechado para modificação através do uso de interfaces, permitindo adicionar novas implementações sem alterar código existente.

```python
class AgentRepositoryInterface(Protocol):
    async def exists(self) -> bool: ...
    async def get_by_name(self, name: str) -> Agent | None: ...
    async def get_by_model(self, model: str) -> Agent | None: ...
```

### Interface Segregation Principle (ISP)
As interfaces são pequenas e específicas para cada tipo de entidade, evitando que implementadores sejam forçados a depender de métodos que não utilizam.

```python
class UserRepositoryInterface(Protocol):
    async def create(self, request: CreateUser) -> User: ...
```

### Dependency Inversion Principle (DIP)
O código depende de abstrações (interfaces) e não de implementações concretas, com injeção de dependências via construtores.

```python
class ChatService:
    def __init__(self, rdb: Redis, 
                 user_repo: UserRepositoryInterface,
                 agent_repo: AgentRepositoryInterface,
                 context_repo: ContextRepositoryInterface, 
                 conversation_repo: ConversationRepositoryInterface,
                 message_repo: MessageRepositoryInterface):
```

## Arquitetura em Camadas
O projeto segue uma arquitetura em camadas bem definida, separando claramente as responsabilidades:

### Camada de Interface
Define contratos para componentes do sistema usando Protocol do typing.

### Camada de Modelos 
Define as entidades de domínio e mapeamentos ORM com SQLAlchemy.

### Camada de Infraestrutura
Implementa o acesso a dados através dos repositórios e provedores de bancos de dados.

### Camada de Serviços
Implementa a lógica de negócios e orquestra operações entre repositórios em services.

### Camada de Controller / Routers
Expõe a API através de routers usando FastAPI.

### Camada de Assistentes IA
Implementa lógica específica para assistentes RAG em assistants.

> **Nota**: O projeto adaptou padrões Python tradicionais para atender requisitos de design orientado a objetos, como o uso extensivo de interfaces via Protocol, injeção de dependência estruturada e tipagem forte, que não são tão comuns em projetos Python tradicionais.