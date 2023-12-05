# T2-INE5418

Trabalho 2 da disciplina de Computação Distribuída
Algoritmo de Eleição de Líder no protocolo IEEE 1394

## Biblioteca

### Requisitos iniciais
* Para utilizar a biblioteca, é preciso ter um arquivo de configuração do tipo JSON, que defina a topologia da rede. Para isso, são definidos os identificadores únicos de cada nodo, seus endereços na rede (IP e porta) e as conexões presentes no grafo. Um exemplo de arquivo pode ser encontrado em `config/network.json`.
* IMPORTANTE:  
    * O grafo não pode ter ciclos
    * Os IDs precisam ser únicos e conhecidos

---

### Utilização
As funções da biblioteca são acessadas através da classe `ElectionProtocolManager`. Para iniciar uma eleição é necessário:

1. Instanciar um objeto da classe `ElectionProtocolManager`, passando como parâmetros o ID do nodo e seu endereço na rede (IP e porta)
2. Iniciar o servidor da instância do `ElectionProtocolManager` e então definir se a instância irá iniciar o processo de eleição ou apenas aguardá-lo.

---

### Aplicação de exemplo

Na nossa aplicação é gerado um número aleatório com um sistema distribuído. O líder recebe os IDs dos outros nós de forma aleatória e no fim reúne os números na ordem recebida.

**Para executar**:

1. Execute o comando `python3 main.py <ID do nó>`. É necessário instanciar todos os nós da rede especificada no arquivo `config/network.json`. O nó que irá iniciar a eleição é o nó com o menor ID.
