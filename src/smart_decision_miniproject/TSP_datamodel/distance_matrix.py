


class DistanceMatrix:
    
    def __init__(self, dimension):
        self.matrix = [[0 for _ in range(dimension)] for _ in range(dimension)]
        self.site_label_dict = {f"site_{i}": i for i in range(dimension)}

    def __str__(self):
        matrix_str = "Distance Matrix:\n"

        # Print column headers
        matrix_str += "    "  # Space for row labels
        for c in self.site_label_dict.keys():
            matrix_str += f"   {c}"
        matrix_str += "\n"
        
        # Print rows with row labels
        for i, row in enumerate(self.matrix):
            row_label = list(self.site_label_dict.keys())[i]
            matrix_str += f" {row_label}  "
            matrix_str += " ".join(f"{dist:3}" for dist in row) + "\n"
        return matrix_str
    
    def __len__(self):
        return len(self.matrix)
    
    def __getitem__(self, index: int) -> list[int]:
        return self.matrix[index]
    
    def __setitem__(self, index: int, value: list[int]) -> None:
        self.matrix[index] = value

    def cal_tour_distance(self, tour: list[int]) -> float:
        total_distance = 0.0
        for i in range(len(tour)):
            from_index = tour[i]
            to_index = tour[(i + 1) % len(tour)]  # Wrap around to the start
            total_distance += self.matrix[from_index][to_index]
        return total_distance

    def set_site_name_list(self, name_list):
        if len(name_list) != len(self.matrix):
            raise ValueError("Name list length must match matrix dimension")
        self.site_label_dict = {name: i for i, name in enumerate(name_list)}
    
    def set_distance_between_sites_by_name(self, site1_name, site2_name, distance):
        site1_index = self.site_label_dict.get(site1_name)
        site2_index = self.site_label_dict.get(site2_name)
        if site1_index is None or site2_index is None:
            raise ValueError("Site name not found")
        self.matrix[site1_index][site2_index] = distance
        self.matrix[site2_index][site1_index] = distance
    
    def get_distance_between_sites_by_name(self, site1_name, site2_name):
        site1_index = self.site_label_dict.get(site1_name)
        site2_index = self.site_label_dict.get(site2_name)
        if site1_index is None or site2_index is None:
            raise ValueError("Site name not found")
        return self.matrix[site1_index][site2_index]
    