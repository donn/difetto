import csv

def get_congestion_scores(csv_path, threshold=80):
    r = csv.reader(open(csv_path))
    next(r)

    gcell_count = 0
    congested_cells = 0
    total_congestion = 0
    total_congestion_sq = 0
    for item in r:
        gcell_count += 1
        congestion = float(item[-1]) / 100
        congested_cells += int(congestion > (threshold / 100))
        total_congestion += congestion
        total_congestion_sq += congestion ** 2
    return total_congestion / gcell_count, congested_cells / gcell_count, total_congestion_sq / gcell_count
