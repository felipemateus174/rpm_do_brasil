from langchain_openai import ChatOpenAI
from browser_use import Agent
from dotenv import load_dotenv
from flask import Flask, request, Response, jsonify
import asyncio
import json

load_dotenv()

app = Flask(__name__)
llm = ChatOpenAI(model="gpt-4o")

async def search_product(codigo: str, marca: str):
    try:
        if not codigo or not marca:
            raise ValueError("Código e marca são obrigatórios")
            
        agent = Agent(
            task=f"""
            Objetivo: Buscar produto na Motion
                URL: https://www.motion.com/

                Produto: {codigo}
                Marca: {marca}

                Instruções:
                1. Acesse https://www.motion.com/
                2. No campo de pesquisa, digite: {codigo}
                3. Aguarde o carregamento completo da página (10 segundos)
                4. Nos resultados, encontre o *produto mais próximo* da marca {marca} com base no código fornecido.
                5. Se houver múltiplos resultados, selecione o *produto mais relevante* considerando a similaridade do código e marca.
                6. Entre na página do produto e capture os seguintes dados:
                    - Nome completo do produto
                    - Código/Part Number
                    - Preço (se disponível)
                    - Status de estoque/disponibilidade
                    - URL direta do produto
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
                7. Caso algum campo não seja encontrado, deixe o valor como "".

                Formato de retorno: JSON válido
                Exemplo válido:
                ```json
                {{
                    "produto": {{
                        "full_product_name": "Nome completo do produto",
                        "part_number": "387A-20024",
                        "price": "R$ 150,00",
                        "stock_status": "Disponível",
                        "direct_url": "https://www.motion.com/produto/387A-20024",
                        "specifications": {{
                            "bore_type": "Straight",
                            "bore_diameter": "25 mm",
                            "outside_diameter": "52 mm",
                            "overall_width": "15 mm",
                            "closure_type": "Open",
                            "snap_ring_included": "Without Snap Ring",
                            "bearing_material": "Bearing steel",
                            "cage_material": "Bearing steel",
                            "cage_type": "Sheet metal",
                            "element_material": "Bearing steel",
                            "fillet_radius": "1 mm",
                            "finish_coating": "Uncoated",
                            "inner_ring_width": "15 mm",
                            "internal_clearance": "CN",
                            "manufacturer_catalog_number": "6205",
                            "max_rpm": "18000 rpm",
                            "precision_rating": "ABEC 3",
                            "radial_dynamic_load_capacity": "3327 lbf",
                            "radial_static_load_capacity": "1754 lbf",
                            "seal_type": "Open",
                            "series": "62",
                            "weight": "0.30 lbs",
                            "product_type": "Radial & Deep Groove Ball Bearings"
                        }}
                    }}
                }}
                Restrições:

                Retornar apenas 1 produto.
                Selecionar o produto mais próximo com base na correspondência entre {codigo} e {marca}.
                Se nenhum produto exato for encontrado, retornar o mais relevante disponível.
                O JSON deve estar devidamente formatado e validado.
            """,

            llm=llm,
        )
        result = await agent.run()
        
        # Ensure result is valid JSON
        if isinstance(result, str):
            result = json.loads(result)
        return result
        
    except Exception as e:
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
    # Cria uma lista de tarefas para buscar cada produto
    tasks = []
    for produto in produtos:
        codigo = produto.get('codigo')
        marca = produto.get('marca')
        quantidade = produto.get('quantidade', 1)
        
        # Para cada produto, adiciona a tarefa à lista
        tasks.append(search_product(codigo, marca))
    
    # Executa todas as buscas em paralelo
    results = await asyncio.gather(*tasks)
    
    # Formata os resultados incluindo a quantidade
    formatted_results = []
    for i, result in enumerate(results):
        try:
            # Converte o resultado para um dicionário, caso seja uma string JSON
            if isinstance(result, str):
                result_dict = json.loads(result)
            else:
                result_dict = result
                
            # Adiciona a quantidade ao resultado
            quantidade = produtos[i].get('quantidade', 1)
            if isinstance(result_dict, dict) and 'produto' in result_dict:
                result_dict['quantidade'] = quantidade
            
            formatted_results.append(result_dict)
        except Exception as e:
            # Em caso de erro, adiciona um resultado de erro
            formatted_results.append({
                'error': f'Erro ao processar produto {produtos[i].get("codigo")}: {str(e)}',
                'raw_result': str(result)
            })
    
    return formatted_results

@app.route('/produtos', methods=['POST'])
def handle_request():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Dados JSON ausentes ou malformados"}), 400
        
        # Validate input structure
        if not isinstance(data, dict) or 'query' not in data or 'produtos' not in data['query']:
            return jsonify({
                "error": "Formato inválido. Esperado: {query: {produtos: [...]}}",
                "received": data
            }), 400
        
        produtos = data['query']['produtos']
        if not produtos or not isinstance(produtos, list):
            return jsonify({"error": "Lista de produtos vazia ou inválida"}), 400
        
        # Validate each product
        for produto in produtos:
            if not isinstance(produto, dict) or 'codigo' not in produto or 'marca' not in produto:
                return jsonify({
                    "error": "Cada produto deve ter 'codigo' e 'marca'",
                    "invalid_product": produto
                }), 400
        
        results = asyncio.run(search_multiple_products(produtos))
        return jsonify({"resultados": results})
            
    except json.JSONDecodeError:
        return jsonify({"error": "JSON inválido"}), 400
    except Exception as e:
        return jsonify({
            "error": "Erro interno do servidor",
            "details": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8085, use_reloader=False)
