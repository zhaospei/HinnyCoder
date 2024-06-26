import argparse

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--create_blank_databases',
        action = 'store_true',
        help = 'create blank databases'
    )

    args = parser.parse_args()

    

if (__name__ == '__main__'):
    main()