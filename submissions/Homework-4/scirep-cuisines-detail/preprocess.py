####
# Tyler Waltze
# 3/20/15
# CS 591
####

import re
import json

# Index map by country
def country(input_file = "map.txt", output_file = "country.json"):
	processed = []
	lineNumber = 0
	with open(input_file, "r") as raw:
		for line in raw:
			lineNumber += 1
			print("line {}".format(lineNumber))

			clean = line.replace("\n", "")

			# Break string into relations
			relation = clean.split("\t")

			# First word is always country
			country = relation.pop(0).lower()

			# First word is always cuisine
			cuisine = relation.pop(0)

			# Add to list of countries
			processed.append({
				"country": country,
				"cuisine": cuisine
			})

	# Encode as json for writing to new file
	encoded = json.dumps(processed)

	# Write to new file
	with open(output_file, "w") as output:
		output.write(encoded)

# Index map by cuisine
def cuisine(input_file = "map.txt", output_file = "cuisine.json"):
	processed = {}
	lineNumber = 0
	with open(input_file, "r") as raw:
		for line in raw:
			lineNumber += 1
			print("line {}".format(lineNumber))

			clean = line.replace("\n", "")

			# Break string into relations
			relation = clean.split("\t")

			# First word is always country
			country = relation.pop(0).lower()

			# First word is always cuisine
			cuisine = relation.pop(0)

			# Add to list of cuisine
			if cuisine in processed:
				processed[cuisine].append(country)
			else:
				processed[cuisine] = [country]

	# Encode as json for writing to new file
	encoded = json.dumps(processed)

	# Write to new file
	with open(output_file, "w") as output:
		output.write(encoded)

# Index ratings by user
def recipes(input_file = "allr_recipes.txt", output_file = "allr.json"):
	processed = []
	lineNumber = 0
	with open(input_file, "r") as raw:
		for line in raw:
			lineNumber += 1
			print("line {}".format(lineNumber))

			clean = line.replace("\n", "")

			# Break string into ingredients
			ingredients = clean.split("\t")

			# First word is always country, not ingredient
			country = ingredients.pop(0).lower()

			boolList = {}
			for ingredient in ingredients:
				boolList[ingredient] = True

			processed.append(dict({
				"country": country
			}.items() + boolList.items()))

	# Encode as json for writing to new file
	encoded = json.dumps(processed)

	# Write to new file
	with open(output_file, "w") as output:
		output.write(encoded)