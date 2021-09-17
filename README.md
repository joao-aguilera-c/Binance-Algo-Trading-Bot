# Binance-Algo-Trading-Bot

Esta é uma versão demo, apenas para teste, do meu algoritmo pessoal de trading em criptomoedas.

## Funcionamento

1. O algoritmo é capaz de rodar diferentes estratégias de análise técnica, em diversos criptoativos de maneira simultânea e em tempo real. Para isso ele verifica o arquivo `strategies_to_run.csv`. Este arquivo é atualizado de tempos em tempos com base em um sistema de backtesting gerado por mim, que testa diferentes estratégias em diversas cryptos e encontra aquelas com o maior potencial de lucro no momento.

2. A partir daí é criado de maneira assíncrona o `kline_listener()`. Um loop `while True:` onde toda a etapa de verificação e execução de ordens acontece. Nesse loop é definido o stream em tempo real do preço dos ativos, e a função `run_strategies()` que verifica potenciais momentos de entrada em trade.

3. Como a binance cobra juros apenas para manter ordens alavancadas abertas, desenvolvi também um módulo de gestão de ordem, que tem a função de guardar os preços de entrada, stop loss e take profit para cada ativo sempre que há um setup válido. E que os executa no momento correto. Este módulo está em `order_management.py`.

Gosto de pensar neste algoritmo como uma plataforma. Nela adiciono novos setups - validados pelas minhas análises e backtests - e ela faz a gestão de todo o resto de maneira autônoma para mim, aumentando assim a minha escala - operando em mais ativos do que poderia - e reduzindo o risco - diversificando e evitando as armadilhas emocionais que o trading proporciona.


---------------------

# Binance-Algo-Trading-Bot (English)

This is a test-only demo version of my personal cryptocurrency trading algorithm.

## Operation

1. The algorithm is capable of running different technical analysis strategies, in several cryptoactives simultaneously and in real time. For this it checks the `strategies_to_run.csv` file. This file is updated from time to time based on a backtesting system generated by me, which tests different strategies in different cryptos and finds those with the greatest profit potential at the moment.

2. From there, `kline_listener()` is created asynchronously. A `while True:` loop where all the step of checking and executing orders takes place. In this loop, the real-time stream of asset prices is defined, and the `run_strategies()` function that checks for potential moments of entry into a trade is defined.

3. As binance charges interest only to keep leveraged orders open, I also developed an order management module, which has the function of saving entry prices, stop loss and take profit for each asset whenever there is a valid setup. And who executes them at the right time. This module is in `order_management.py`.

I like to think of this algorithm as a platform. In it I add new setups - validated by my analysis and backtests - and it manages everything else autonomously for me, thus increasing my scale - operating in more assets than I could - and reducing risk - diversifying and avoiding emotional pitfalls that trading provides. 
