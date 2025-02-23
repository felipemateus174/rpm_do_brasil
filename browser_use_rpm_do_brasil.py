from langchain_openai import ChatOpenAI
from browser_use import Agent, BrowserConfig
from dotenv import load_dotenv
from flask import Flask, request, jsonify
import asyncio
import json
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.json import JSON

console = Console()

load_dotenv()

app = Flask(__name__)
llm = ChatOpenAI(model="gpt-4o")

async def search_product(codigo: str, marca: str):
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
            markdown
            Copiar
            Editar 
        """,

        llm=llm,
    )
    result = await agent.run()
    return result

@app.route('/produtos', methods=['POST'])
def handle_request():
    try:
        data = request.get_json()
        if not data:
            rprint("[red]Erro: Dados JSON ausentes[/red]")
            return jsonify({"error": "Dados JSON ausentes"}), 400
            
        codigo = data.get('codigo')
        marca = data.get('marca')
        
        if not codigo or not marca:
            rprint("[red]Erro: Parâmetros obrigatórios faltando[/red]")
            return jsonify({'error': 'Parâmetros obrigatórios faltando: codigo e marca'}), 400
        
        # Print search parameters
        console.print(Panel(f"[yellow]Buscando produto:[/yellow]\nCódigo: {codigo}\nMarca: {marca}", 
                          title="Parâmetros de Busca"))
            
        result = asyncio.run(search_product(codigo, marca))
        
        # Improved result handling with rich printing
        try:
            if isinstance(result, str):
                try:
                    json_data = json.loads(result)
                    console.print(Panel(JSON(json_data), title="Resultado da Busca"))
                except json.JSONDecodeError:
                    console.print(Panel(f"[white]{result}[/white]", title="Resultado da Busca"))
            elif hasattr(result, '__dict__'):
                console.print(Panel(JSON(result.__dict__), title="Resultado da Busca"))
            else:
                console.print(Panel(f"[white]{str(result)}[/white]", title="Resultado da Busca"))
            
            return jsonify({"status": "success"})
            
        except json.JSONDecodeError:
            console.print(Panel(f"[white]{str(result)}[/white]", title="Resultado (Formato não-JSON)"))
            return jsonify({"status": "success"})
        
    except Exception as e:
        console.print(f"[red]Erro interno: {str(e)}[/red]")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8085, use_reloader=False)
