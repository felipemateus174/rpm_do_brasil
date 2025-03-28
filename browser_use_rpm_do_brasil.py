from langchain_openai import ChatOpenAI
from browser_use import Agent  # Assumo que isso é um módulo customizado
from dotenv import load_dotenv
from flask import Flask, request, Response, jsonify
import asyncio
import json
import logging

# Configurar logging para depuração
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)
llm = ChatOpenAI(model="gpt-4o")

async def search_product(codigo: str, marca: str):
    try:
        logger.debug(f"search_product recebeu: codigo={codigo}, marca={marca}")
        
        if not codigo or not marca:
            raise ValueError(f"Código e marca são obrigatórios. Recebido: codigo='{codigo}', marca='{marca}'")
            
        agent = Agent(
            task=f"""# INSTRUÇÕES PARA A EXECUÇÃO DA PESQUISA AUTOMATIZADA

## 1. Objetivo:
Este script realiza pesquisas em múltiplos sites de fornecedores, buscando produtos com base no código e marca informados, seguindo uma ordem específica até encontrar um preço válido ou esgotar os fornecedores.

Produto: {codigo}
Marca: {marca}

## 2. Fluxo de Execução:

### Lista de Fornecedores (em ordem de prioridade):
1. Motion: https://www.motion.com/
2. Abecom: https://www.loja.abecom.com.br/loja/busca.php?loja=835310&palavra_busca=SL1818%2F210
3. Quality: https://www.qualitybearingsonline.com/
4. Misumi: https://us.misumi-ec.com/
5. Rhia: https://shop.rhia.de/de/
6. Samflex Estrela: https://rodavigo.net/pt
7. Misumi UK: https://uk.misumi-ec.com/

### Passos:

Motion:
1. Acesse o site do fornecedor atual (começando pelo primeiro da lista).
2. Localize o campo de pesquisa e insira {codigo}.
3. Execute a pesquisa pressionando "Enter" ou acionando o botão de busca.
4. Aguarde o carregamento completo da página (mínimo 10 segundos).
5. Verifique os resultados da busca:
   - Priorize produtos com a marca mais próxima de {marca}.
   - Caso não haja um produto exato, selecione o mais relevante pelo código.
6. Entre na página do produto selecionado e extraia todas as informações disponíveis.
7. Verifique o preço:
   - Se o preço for encontrado e for um valor válido (diferente de "", "indisponível", "sob consulta" ou similar), finalize a pesquisa e retorne os dados.
   - Se o preço não for encontrado ou for inválido (como "", "indisponível", "sob consulta"), passe para o próximo fornecedor da lista e repita os passos.
8. Continue até encontrar um preço válido ou esgotar todos os fornecedores.

abecom:
1. Acesse o site do fornecedor atual (começando com essa URL https://www.loja.abecom.com.br/loja/busca.php?loja=835310&palavra_busca=SL1818%2F210).
2. Aguarde até 5 segundos para fechar qualquer modal inicial (como um modal de cookies), verificando o elemento com o XPath "//button[contains(text(), 'Ok, entendi') or contains(text(), 'Aceitar') or contains(@class, 'cookie') or contains(@id, 'cookie')]".
   - Se encontrado, clique no botão para fechar o modal.
   - Aguarde 2 segundos para garantir que o modal foi fechado.
3. Aguarde até 15 segundos para o modal de Newsletter aparecer, verificando o elemento com o XPath "//div[contains(@class, 'modal-info') and .//div[contains(@class, 'newsletter')]]".
   - Se o modal for encontrado:
     a. Localize o botão de fechar com o XPath "//div[contains(@class, 'modal-info')]//div[contains(@class, 'close-icon')]".
     b. Clique no botão de fechar.
     c. Aguarde 2 segundos e verifique se o modal não está mais visível (usando o mesmo XPath do modal).
     d. Se o modal ainda estiver visível, tente clicar novamente ou registre um erro e continue.
   - Se o modal não for encontrado após 15 segundos, continue para o próximo passo.
4. Localize o campo de pesquisa com o XPath "//input[contains(@placeholder, 'Pesquisar') or @id='search' or @name='q']" e insira {codigo}.
5. Execute a pesquisa clicando no botão de busca com o XPath "//button[contains(@class, 'search') or contains(@type, 'submit') and (text()='Pesquisar' or contains(@aria-label, 'pesquisar'))]".
6. Aguarde o carregamento completo da página (mínimo 10 segundos).
7. Verifique os resultados da busca:
8. Priorize produtos com a marca mais próxima de {marca} (se houver).

## 3. Dados a Serem Extraídos:

- Nome completo do produto
- Código/Part Number
- Preço (obrigatório, deve ser um valor numérico ou formatado como moeda)
- Status de estoque/disponibilidade
- URL direta do produto
- Especificações técnicas:
  - Bore Type
  - Bore Diameter
  - Outside Diameter
  - Overall Width
  - Closure Type
  - Snap Ring Included
  - Bearing Material
  - Cage Material
  - Cage Type
  - Description
  - Element Material
  - Fillet Radius
  - Finish Coating
  - Inner Ring Width
  - Internal Clearance
  - Manufacturer Catalog Number
  - Manufacturer UPC Number
  - Max RPM
  - Operating Temperature Range
  - Precision Rating
  - Radial Dynamic Load Capacity
  - Radial Static Load Capacity
  - Seal Type
  - Series
  - Weight
  - Product Type

## 4. Formato da Saída:

Retornar JSON válido no seguinte formato:

{{
    "produto": {{
        "full_product_name": "",
        "part_number": "",
        "price": "",  // Deve ser um valor válido (ex.: "123.45", "$123.45", "€123,45")
        "stock_status": "",
        "direct_url": "",
        "specifications": {{
            "bore_type": "",
            "bore_diameter": "",
            "outside_diameter": "",
            "overall_width": "",
            "closure_type": "",
            "snap_ring_included": "",
            "bearing_material": "",
            "cage_material": "",
            "cage_type": "",
            "description": "",
            "element_material": "",
            "fillet_radius": "",
            "finish_coating": "",
            "inner_ring_width": "",
            "internal_clearance": "",
            "manufacturer_catalog_number": "",
            "manufacturer_upc_number": "",
            "max_rpm": "",
            "operating_temperature_range": "",
            "precision_rating": "",
            "radial_dynamic_load_capacity": "",
            "radial_static_load_capacity": "",
            "seal_type": "",
            "series": "",
            "weight": "",
            "product_type": ""
        }},
        "fornecedor": ""
    }}
}}

## 5. Regras e Observações:

- Aguardar carregamento completo da página (10 segundos mínimo).
- Se um campo não for encontrado, usar "", exceto para o preço, que é obrigatório.
- Retornar apenas 1 produto mais relevante por fornecedor.
- JSON deve estar devidamente formatado e validado.
- Priorizar correspondência exata de marca e código.
- Adicionar o campo "fornecedor" no JSON com o nome do site onde o produto foi encontrado.
- Parar a pesquisa SOMENTE quando um preço válido for encontrado em um fornecedor.
- Se o preço não for válido (ex.: "", "indisponível", "sob consulta"), continuar para o próximo fornecedor.
- Se nenhum fornecedor tiver um preço válido, retornar um JSON com "price": "não encontrado" e os dados do último fornecedor pesquisado.
""",
            llm=llm,
        )
        result = await agent.run()
        
        # Return the raw result as string without JSON parsing
        return {
            "raw_result": str(result),
            "codigo": codigo,
            "marca": marca
        }
        
    except Exception as e:
        logger.error(f"Erro em search_product: {str(e)}")
        return {
            "error": f"Erro ao buscar produto {codigo}: {str(e)}",
            "codigo": codigo,
            "marca": marca
        }

async def search_multiple_products(produtos):
    """
    Busca múltiplos produtos em paralelo.
    
    Args:
        produtos: Lista de dicionários com 'codigo', 'marca' e 'quantidade'
        
    Returns:
        Lista de resultados para cada produto
    """
    if not produtos:
        raise ValueError("Lista de produtos vazia")

    tasks = []
    for i, produto in enumerate(produtos):
        codigo = produto.get('codigo')
        marca = produto.get('marca')
        
        # Improved validation
        if not codigo:
            raise ValueError(f"Produto {i+1}: código e marca são obrigatórios. Recebido: {produto}")
            
        quantidade = produto.get('quantidade', 1)
        logger.debug(f"Processando produto {i+1}: codigo={codigo}, marca={marca}, quantidade={quantidade}")
        tasks.append(search_product(codigo, marca))
    
    # Executa todas as buscas em paralelo
    results = await asyncio.gather(*tasks)
    
    # Formata os resultados incluindo a quantidade
    formatted_results = []
    for i, result in enumerate(results):
        try:
            quantidade = produtos[i].get('quantidade', 1)
            # Add raw result directly without JSON parsing
            formatted_results.append({
                "raw_result": str(result),
                "codigo": produtos[i].get('codigo'),
                "marca": produtos[i].get('marca'),
                "quantidade": quantidade
            })
        except Exception as e:
            logger.error(f"Erro ao formatar resultado {i}: {str(e)}")
            formatted_results.append({
                'error': f'Erro ao processar produto {produtos[i].get("codigo")}: {str(e)}',
                'raw_result': str(result)
            })
    
    return formatted_results

@app.route('/produtos', methods=['POST'])
def handle_request():
    try:
        data = request.get_json()
        logger.debug(f"Dados recebidos: {data}")
        
        # Improved validation with more specific error messages
        if not data:
            return jsonify({"error": "Dados JSON ausentes"}), 400
            
        if not isinstance(data, dict):
            return jsonify({"error": "Dados devem ser um objeto JSON"}), 400
            
        if 'query' not in data:
            return jsonify({"error": "Campo 'query' não encontrado"}), 400
            
        if not isinstance(data['query'], dict):
            return jsonify({"error": "Campo 'query' deve ser um objeto"}), 400
            
        if 'produtos' not in data['query']:
            return jsonify({"error": "Campo 'produtos' não encontrado em 'query'"}), 400
            
        produtos = data['query']['produtos']
        
        if not isinstance(produtos, list):
            return jsonify({"error": "Campo 'produtos' deve ser uma lista"}), 400
            
        if not produtos:
            return jsonify({"error": "Lista de produtos está vazia"}), 400

        # Log validation success
        logger.info(f"Validação bem sucedida. Processando {len(produtos)} produtos")
        
        results = asyncio.run(search_multiple_products(produtos))
        return jsonify({"resultados": results})
            
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao decodificar JSON: {str(e)}")
        return jsonify({"error": "JSON inválido", "details": str(e)}), 400
    except Exception as e:
        logger.error(f"Erro na rota /produtos: {str(e)}")
        return jsonify({
            "error": "Erro interno do servidor",
            "details": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8085, use_reloader=False)
