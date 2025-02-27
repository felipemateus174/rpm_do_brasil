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
        # Log dos valores recebidos para verificar se estão chegando corretamente
        logger.debug(f"search_product recebeu: codigo={codigo}, marca={marca}")
        
        # Validação mais explícita para evitar falsos positivos
        if codigo is None or marca is None or codigo == "" or marca == "":
            raise ValueError("Código e marca são obrigatórios")
            
        agent = Agent(
            task=f"""# INSTRUÇÕES PARA A EXECUÇÃO DA PESQUISA AUTOMATIZADA

## 1. Objetivo:
Este script realiza pesquisas no site https://www.motion.com/, buscando produtos com base no código e marca informados.

Produto: {codigo}
Marca: {marca}

## 2. Fluxo de Execução:

1. *Acesse o site*: https://www.motion.com/
2. *Localize o campo de pesquisa* e insira {codigo}
3. *Execute a pesquisa* pressionando "Enter" ou acionando o botão de busca
4. *Aguarde o carregamento completo da página* (*mínimo 10 segundos*)
5. *Verifique os resultados da busca*:
   - Priorize produtos com a *marca mais próxima* de {marca}
   - Caso não haja um produto exato, selecione o mais relevante pelo *código*
6. *Entre na página do produto selecionado* e extraia todas as informações disponíveis

## 3. Dados a Serem Extraídos:

- Nome completo do produto
- Código/Part Number
- Preço (se disponível)
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
        "price": "",
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
        }}
    }}
}}

## 5. Regras e Observações:

✅ Aguardar carregamento completo da página (10 segundos mínimo)
✅ Se campo não encontrado, usar ""
✅ Retornar apenas 1 produto mais relevante
✅ JSON deve estar devidamente formatado e validado
✅ Priorizar correspondência exata de marca e código
""",
            llm=llm,
        )
        result = await agent.run()
        
        # Log do resultado bruto para verificar o que o Agent retorna
        logger.debug(f"Resultado bruto do Agent: {result}")
        
        # Garantir que o resultado seja um JSON válido
        if isinstance(result, str):
            result = json.loads(result)
        return result
        
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
    tasks = []
    for produto in produtos:
        codigo = produto.get('codigo')
        marca = produto.get('marca')
        quantidade = produto.get('quantidade', 1)
        
        # Log para verificar os valores antes de chamar search_product
        logger.debug(f"Chamando search_product com codigo={codigo}, marca={marca}")
        tasks.append(search_product(codigo, marca))
    
    # Executa todas as buscas em paralelo
    results = await asyncio.gather(*tasks)
    
    # Formata os resultados incluindo a quantidade
    formatted_results = []
    for i, result in enumerate(results):
        try:
            if isinstance(result, str):
                result_dict = json.loads(result)
            else:
                result_dict = result
                
            quantidade = produtos[i].get('quantidade', 1)
            if isinstance(result_dict, dict) and 'produto' in result_dict:
                result_dict['quantidade'] = quantidade
            
            formatted_results.append(result_dict)
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
        # Log dos dados recebidos para verificar o JSON bruto
        logger.debug(f"Dados recebidos: {data}")
        
        if not data:
            return jsonify({"error": "Dados JSON ausentes ou malformados"}), 400
        
        if not isinstance(data, dict) or 'query' not in data or 'produtos' not in data['query']:
            return jsonify({
                "error": "Formato inválido. Esperado: {query: {produtos: [...]}}",
                "received": data
            }), 400
        
        produtos = data['query']['produtos']
        # Log dos produtos extraídos
        logger.debug(f"Produtos extraídos: {produtos}")
        
        if not produtos or not isinstance(produtos, list):
            return jsonify({"error": "Lista de produtos vazia ou inválida"}), 400
        
        for produto in produtos:
            if not isinstance(produto, dict) or 'codigo' not in produto or 'marca' not in produto:
                return jsonify({
                    "error": "Cada produto deve ter 'codigo' e 'marca'",
                    "invalid_product": produto
                }), 400
        
        results = asyncio.run(search_multiple_products(produtos))
        return jsonify({"resultados": results})
            
    except json.JSONDecodeError:
        logger.error("Erro ao decodificar JSON")
        return jsonify({"error": "JSON inválido"}), 400
    except Exception as e:
        logger.error(f"Erro na rota /produtos: {str(e)}")
        return jsonify({
            "error": "Erro interno do servidor",
            "details": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8085, use_reloader=False)