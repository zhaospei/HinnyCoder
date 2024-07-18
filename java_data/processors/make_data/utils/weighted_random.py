import argparse

import numpy as np
import pandas as pd

# Set a random seed for reproducibility
np.random.seed(11)


# Function to select a random row based on weights
def weighted_random_row(group):
    return group.sample(n=1, weights=group["len_func_body"])
    # return group.loc[group["len_func_body"].idxmax()]


def main(args):
    df = pd.read_parquet(args.input)
    # Group by 'group' column and apply the weighted_random_row function
    random_rows_weighted = df.groupby(by="relative_path").apply(
        weighted_random_row
    )
    random_rows_weighted.reset_index(drop=True, inplace=True)
    random_rows_weighted.to_parquet(args.output)
    print("\nRandom row from each group (with weights):")
    print(random_rows_weighted)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", dest="input")
    parser.add_argument("--output", dest="output")
    args = parser.parse_args()
    main(args)
