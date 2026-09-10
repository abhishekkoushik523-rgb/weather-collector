from duplicate_detection.location import distance_km


# Two reports very close to each other in Whitefield
coord_a = (13.0078, 77.7512)
coord_b = (13.0080, 77.7515)

distance = distance_km(coord_a, coord_b)

print("Distance between A and B:", round(distance, 3), "km")


# Two reports in completely different cities
coord_c = (28.6139, 77.2090)

distance_far = distance_km(coord_a, coord_c)

print("Distance between A and C:", round(distance_far, 3), "km")