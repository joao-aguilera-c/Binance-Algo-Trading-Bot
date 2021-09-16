# Binance-Algo-Trading-Bot

Esta é uma versão demo, apenas para teste, do meu algoritmo pessoal de trading em criptomoedas.

## Funcionamento

1. O algoritmo é capaz de rodar diferentes estratégias de análise técnica, em diversos criptoativos de maneira simultânea e em tempo real. Para isso ele verifica o arquivo `strategies_to_run.csv`. Este arquivo é atualizado de tempos em tempos com base em um sistema de backtesting gerado por mim, que testa diferentes estratégias em diversas cryptos e encontra aquelas com o maior potencial de lucro no momento.

2. A partir daí é criado de maneira assíncrona o `kline_listener()`. Um loop `while True:` onde toda a etapa de verificação e execução de ordens acontece. Nesse loop é definido o stream em tempo real do preço dos ativos, e a função `run_strategies()` que verifica potenciais momentos de entrada em trade.

3. Como a binance cobra juros apenas para manter ordens alavancadas abertas, desenvolvi também um módulo de gestão de ordem, que tem a função de guardar os preços de entrada, stop loss e take profit para cada ativo sempre que há um setup válido. E que os executa no momento correto. Este módulo está em `order_management.py`.

Gosto de pensar neste algoritmo como uma plataforma. Nela adiciono novos setups - validados pelas minhas análises e backtests - e ela faz a gestão de todo o resto de maneira autônoma para mim, aumentando assim a minha escala - operando em mais ativos do que poderia - e reduzindo o risco - diversificando e evitando as armadilhas emocionais que o trading proporciona.
