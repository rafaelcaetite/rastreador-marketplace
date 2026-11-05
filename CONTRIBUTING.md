# Contribuindo com o Rastreador de Marketplace

Obrigado pelo interesse em contribuir! Este projeto foi desenvolvido seguindo princípios de Clean Code, arquitetura modular e boas práticas de engenharia de software.

## Como Contribuir

1. **Faça um Fork** do repositório.
2. **Crie uma branch** para sua feature ou correção:
   ```bash
   git checkout -b feature/novo-marketplace
   ```
3. **Escreva testes** unitários cobrindo as alterações em `tests/`.
4. **Execute a suite de testes**:
   ```bash
   pytest
   ```
5. **Abra um Pull Request** com descrição clara da melhoria proposta.

## Como Adicionar um Novo Marketplace

O projeto utiliza o padrão Strategy via `BaseScraper`. Para plugar um novo marketplace (ex: Amazon, Enjoei, etc.):

1. Crie uma nova classe em `scraper/novo_marketplace_scraper.py` herdando de `BaseScraper`:
   ```python
   from scraper.base_scraper import BaseScraper
   from models import AdItem

   class NovoMarketplaceScraper(BaseScraper):
       async def search(self, query: str) -> list[AdItem]:
           # Lógica de extração normalizada
           ...
   ```
2. Instancie o novo coletor no `DealPipeline` em `pipeline.py`.
3. Escreva o teste unitário correspondente em `tests/`.
