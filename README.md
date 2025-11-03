# Austin.S---Forecasting
Forecasting
Adaptive Transformer–RL Framework for Sentiment-Driven Financial Forecasting
<img width="148" height="20" alt="image" src="https://github.com/user-attachments/assets/48e2c19c-441c-457c-869e-34da182f08d0" />
<img width="82" height="20" alt="image" src="https://github.com/user-attachments/assets/d2b57bb9-5ca6-4ceb-9966-bcc66dfa0832" />
<img width="86" height="20" alt="image" src="https://github.com/user-attachments/assets/39574e74-3569-4668-8a9f-a47c444f1b68" />

## Overview

This repository contains the official implementation of the hybrid framework proposed in our MDPI Forecasting 2025 paper:
## "From Market Volatility to Predictive Insight: An Adaptive Transformer–RL Framework for Sentiment-Driven Financial Time-Series Forecasting"
The framework integrates domain-specific sentiment analysis, heterogeneous prediction models (SVR + Transformer variants), and Deep Q-Network (DQN)-driven dynamic ensembling to address the challenges of financial time-series forecasting (e.g., market volatility, nonlinear regimes, and sentiment-quant data fusion).

## Paper Abstract

Financial time-series prediction remains challenging due to market volatility, nonlinear dynamics, and the complex interplay between quantitative indicators and investor sentiment. Traditional models (e.g., ARIMA, GARCH) fail to capture textual sentiment, while static deep learning methods cannot adapt to market regime shifts (bull/bear/consolidation).

## Our proposed framework:

1. Constructs a domain-specific financial sentiment dictionary (16,673 entries) with up to 97.35% forum title classification accuracy.
2. Fuses historical price data and investor sentiment into a hybrid model stack (SVR + 3 Transformer variants).
3. Uses a DQN agent to dynamically ensemble predictions, adapting to real-time market conditions.
   
Experiments on diverse assets (China Unicom, CSI 100, Corn Futures, Amazon) show the framework outperforms benchmark and state-of-the-art models, achieving the lowest RMSE across volatile and stable markets.
## Key Contributions
1. Domain-Specific Sentiment Dictionary: Built via SnowNLP and Word2Vec, tailored for financial investor forums (16,673 entries, 97.35% classification accuracy).
2. Heterogeneous Model Stack: Combines SVR (linear trends) with 3 Transformer variants (nonlinear dependencies):
* Base-Transformer (single-layer encoder for moderate markets)
* Multi-Transformer (3-layer encoder for volatile markets)
* Bi-Transformer (bidirectional encoder for contextual feature extraction)
3. DQN-Driven Dynamic Ensembling: Adaptively weights model outputs based on market volatility (reward = -MSE), outperforming static ensembles (arithmetic mean, weighted average).
4. Multi-Market Generalization: Validated on equities, indices, and commodities (RMB/USD-denominated assets) across global events (Russia–Ukraine war, COVID-19).
## Repository Structure
## 仓库结构
```plaintext
.
├── data/                  # 数据处理脚本和样本数据
│   ├── raw/               # 原始数据（金融价格 + 论坛文本）
│   ├── processed/         # 预处理数据（归一化价格 + 情感分数）
│   ├── dictionary/        # 金融情感词典（16k 条目）
│   └── data_loader.py     # 数据加载和预处理管道
├── models/                # 核心模型实现
│   ├── sentiment/         # 情感分析（SnowNLP + Word2Vec）
│   ├── predictors/        # 基础预测模型（SVR + Transformer 变体）
│   │   ├── svr.py
│   │   ├── base_transformer.py
│   │   ├── multi_transformer.py
│   │   └── bi_transformer.py
│   └── dqn_ensemble.py    # 基于 DQN 的动态集成
├── experiments/           # 实验脚本
│   ├── train.py           # 模型训练管道
│   ├── evaluate.py        # 评估（RMSE/MAE/MAPE）
│   └── visualize.py       # 结果可视化（时间序列图、SHAP 分析）
├── utils/                 # 辅助函数
│   ├── metrics.py         # 评估指标（MSE, RMSE, MAE, MAPE）
│   └── preprocessing.py   # 文本清洗（正则、停用词移除、结巴分词）
├── requirements.txt       # 依赖项
├── LICENSE                # MIT 许可证
└── README.md              # 项目文档
