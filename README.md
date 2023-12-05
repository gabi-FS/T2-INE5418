# T2-INE5418

Trabalho 2 da disciplina de Computação Distribuída
Algoritmo de Eleição de Líder no protocolo IEEE 1394

## Biblioteca

### Requisitos iniciais
* Para utilizar a biblioteca, é preciso ter um arquivo de configuração do tipo JSON, que defina a topologia da rede. Para isso, são definidos os identificadores únicos de cada nó, seus endereços na rede (IP e porta) e as conexões presentes no grafo. Um exemplo de arquivo pode ser encontrado em `config/network.json`.

* IMPORTANTE:
    * O grafo não pode ter ciclos
    * Os IDs precisam ser únicos e conhecidos

---

### Utilização
As funções da biblioteca são acessadas através da classe `ElectionProtocolManager`. Para iniciar uma eleição é necessário:

1. Instanciar um objeto `Network`, que recebe como parâmetro o caminho para o arquivo de configuração
2. Instanciar um objeto da classe `ElectionProtocolManager`, passando como parâmetros o ID do nó, seu endereço na rede (IP e porta) e seus vizinhos
    * O endereço do nó atual pode ser obtido com a função `get_node_election_address` do objeto `Network`
    * Os vizinhos podem ser obtidos com a função `get_election_neighbors` do objeto `Network`
3. Chamar a função `start_server` a partir da instância de `ElectionProtocolManager` para preparar as conexões para a eleição
4. A partir do objeto de `ElectionProtocolManager`:  
    * Um dos nós deve chamar a função `start_election`
    * Os outros nós devem chamar `wait_for_election`

## Aplicação irá iniciar o processo de eleição ou apenas aguardá-lo.

### Aplicação de exemplo

Na nossa aplicação é gerado um número aleatório com um sistema distribuído. O líder recebe os IDs dos outros nós de forma aleatória e no fim reúne os números na ordem recebida.

**Para executar**: Execute o comando `python3 main.py <ID do nó>`. É necessário instanciar todos os nós da rede especificada no arquivo `config/network.json`. O nó que irá iniciar a eleição é o nó com o menor ID. É recomendado que os nós sejam inicializados em ordem decrescente no exemplo fornecido. No fim da execução um número aleatório é exibido no terminal do nó líder.
