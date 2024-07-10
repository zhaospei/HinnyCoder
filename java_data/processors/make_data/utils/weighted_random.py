import numpy as np
import pandas as pd

# Set a random seed for reproducibility
np.random.seed(11)


# Function to select a random row based on weights
def weighted_random_row(group):
    return group.sample(n=1, weights=group["len_func_body"])
    # return group.loc[group["len_func_body"].idxmax()]


if __name__ == "__main__":
    df = pd.read_parquet("/home/hieuvd/lvdthieu/java-dataset-v3.parquet")
    # Group by 'group' column and apply the weighted_random_row function
    random_rows_weighted = df.groupby(by="relative_path").apply(
        weighted_random_row
    )
    random_rows_weighted.reset_index(drop=True, inplace=True)
    random_rows_weighted.to_parquet(
        "/home/hieuvd/lvdthieu/java-data-v5.parquet"
    )
    print("\nRandom row from each group (with weights):")
    print(random_rows_weighted)
