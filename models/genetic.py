import logging
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from deap import algorithms, base, creator, tools
from feast import FeatureStore

from features.indicators import rsi

# --- Configuration ---
FEAST_REPO_PATH = "../features/feature_repo"
INITIAL_CAPITAL = 100000
POPULATION_SIZE = 50
CROSSOVER_PROB = 0.5
MUTATION_PROB = 0.2
NUM_GENERATIONS = 20

# --- DEAP Setup ---
creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", list, fitness=creator.FitnessMax)

toolbox = base.Toolbox()

# Gene generator
toolbox.register("attr_rsi_buy", random.uniform, 10, 40)
toolbox.register("attr_rsi_sell", random.uniform, 60, 90)

# Individual (chromosome) generator
toolbox.register(
    "individual",
    tools.initCycle,
    creator.Individual,
    (toolbox.attr_rsi_buy, toolbox.attr_rsi_sell),
    n=1,
)

# Population generator
toolbox.register("population", tools.initRepeat, list, toolbox.individual)


def evaluate(individual, data: pd.DataFrame, n_splits: int = 5) -> tuple[float]:
    """Fitness function with walk-forward backtest."""
    rsi_buy_threshold, rsi_sell_threshold = individual

    fold_size = len(data) // n_splits
    all_returns = []
    total_trades = 0

    for i in range(n_splits - 1):
        fold_start_index = i * fold_size
        fold_end_index = (i + 1) * fold_size

        validation_df = data.iloc[fold_start_index:fold_end_index].copy()

        # 1. Generate signals
        validation_df['rsi'] = rsi(validation_df['close'], period=14)
        validation_df['signal'] = 0
        validation_df.loc[validation_df['rsi'] < rsi_buy_threshold, 'signal'] = 1
        validation_df.loc[validation_df['rsi'] > rsi_sell_threshold, 'signal'] = -1

        # 2. Backtest on the fold
        validation_df['market_return'] = validation_df['close'].pct_change()
        validation_df['strategy_return'] = validation_df['market_return'] * validation_df['signal'].shift(1)

        all_returns.append(validation_df['strategy_return'])
        total_trades += (validation_df['signal'].diff().fillna(0) != 0).sum()

    # 3. Combine returns and calculate fitness
    if not all_returns:
        return (0.0,)

    combined_returns = pd.concat(all_returns).dropna()

    if combined_returns.empty:
        return (0.0,)

    # 4. Overfitting penalty
    trade_penalty = max(0, (total_trades - (n_splits * 20)) * 0.001)

    # 5. Fitness = Annualized Return
    annualized_return = combined_returns.mean() * 252
    penalized_return = annualized_return * (1 - trade_penalty)

    return (penalized_return,)


def run_genetic_algorithm():
    """Main GA loop."""
    # Load data
    store = FeatureStore(repo_path=FEAST_REPO_PATH)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * 2) # More data for walk-forward

    entity_df = pd.DataFrame({"symbol": ["GOOGL"], "event_timestamp": [end_date]})
    features_to_load = ["instrument_features:close_price"]

    logging.info("Loading data for GA...")
    data_df = store.get_historical_features(entity_df=entity_df, features=features_to_load).to_df()
    data_df = data_df.rename(columns={"close_price": "close"})
    data_df = data_df.set_index('event_timestamp').sort_index()

    # Register DEAP operators
    toolbox.register("evaluate", evaluate, data=data_df)
    toolbox.register("mate", tools.cxTwoPoint)
    toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=5.0, indpb=0.2) # Increased sigma for more exploration
    toolbox.register("select", tools.selTournament, tournsize=3)

    # Run the GA
    logging.info("Starting genetic algorithm...")
    population = toolbox.population(n=POPULATION_SIZE)

    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", np.mean)
    stats.register("std", np.std)
    stats.register("min", np.min)
    stats.register("max", np.max)

    hof = tools.HallOfFame(1)

    algorithms.eaSimple(
        population,
        toolbox,
        cxpb=CROSSOVER_PROB,
        mutpb=MUTATION_PROB,
        ngen=NUM_GENERATIONS,
        stats=stats,
        halloffame=hof,
        verbose=True,
    )

    logging.info(f"Best individual is: {hof[0]} with fitness: {hof[0].fitness.values[0]}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_genetic_algorithm()
