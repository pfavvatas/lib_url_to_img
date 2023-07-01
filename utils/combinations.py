import json

def generate_combinations_reversed(node, parent_tags, parent_tags_by_id, combinations):
    try:
        #Remove root node
        if(node.depth != 0):
            current_tags = parent_tags + [node.tag_name] #To be deleted
            current_tags_by_id = parent_tags_by_id + [str(node.unique_id)]
        else:
            current_tags = parent_tags #To be deleted
            current_tags_by_id = parent_tags_by_id

        if not node.children:
            combination = ' > '.join(current_tags) #To be deleted
            combination_by_id = '-'.join(current_tags_by_id)
            reversed_list = list(reversed(current_tags)) #To be deleted
            reversed_list_by_id = list(reversed(current_tags_by_id))
            sub_combinations = [reversed_list[:i] for i in range(1, len(reversed_list) + 1)] #To be deleted
            sub_combinations_by_id = [reversed_list_by_id[:i] for i in range(1, len(reversed_list_by_id) + 1)]
            combinations[combination_by_id] = {
                'reversed': reversed_list, #To be deleted
                'reversed_by_id': reversed_list_by_id,
                'combinations': [(sub_comb, len(sub_comb)) for sub_comb in sub_combinations], #To be deleted
                'combinations_by_id': [(sub_comb_by_id, len(sub_comb_by_id)) for sub_comb_by_id in sub_combinations_by_id]
            }
            return

        for child in reversed(node.children):
            generate_combinations_reversed(child, current_tags, current_tags_by_id, combinations)
    except Exception as e:
        print(e)

def search_combinations_by_level(combinations_reverse, desired_level):
    try:
        desired_level = int(desired_level)
    except ValueError:
        print("\033[91m [search_combinations_by_level] WARNING: You did not enter a valid integer. \033[0m")

    search_results = []

    for combinations_by_id, data in combinations_reverse.items():
        found_match = False

        for sub_comb, level in data['combinations_by_id']:
            if level == desired_level:
                search_results.append((sub_comb))
                found_match = True
                break

        if not found_match:
            for sub_comb, level in data['combinations_by_id']:
                if level < desired_level:
                    search_results.append((sub_comb))
                    found_match = True
                    break

        if not found_match:
            for sub_comb, level in reversed(data['combinations_by_id']):
                if level > desired_level:
                    continue
                if level <= desired_level:
                    search_results.append((sub_comb))
                    found_match = True
                    break

    return search_results

# def search_multiple_levels(combinations_reverse, desired_levels):
#     results = []

#     for level in desired_levels:
#         combinations = search_combinations_by_level(combinations_reverse, level)
#         results.append({'level': str(level), 'combinations': combinations})

#     return results

def get_combinations_tags_by_unique_id(data):
    # Use list comprehension to collect all combinations
    all_combinations = [combination for obj in data for combination in obj['combinations']]

    return all_combinations

def get_combinations_keys_ordered(combinations_keys, combinations):
    with open('configuration/tags.json') as config_file:
        config_data = json.load(config_file)
        tag_order = config_data.get('tag_order', {})  # Use an empty dictionary if 'tag_order' doesn't exist

       # Compute combinations_keys_ordered
        combinations_keys_ordered = []
        for key, combination in zip(combinations_keys, combinations):
            if key in tag_order:
                combinations_keys_ordered.append((key, combination))
            else:
                combinations_keys_ordered.append((key, combination))
                tag_order[key] = max(tag_order.values(), default=0) + 1

        # Sort combinations_keys_ordered based on tag_order
        combinations_keys_ordered.sort(key=lambda x: tag_order.get(x[0], float('inf')))

    # Update the tag_order in the configuration file
    config_data['tag_order'] = tag_order
    with open('configuration/tags.json', 'w') as config_file:
        json.dump(config_data, config_file, indent=4)

    return combinations_keys_ordered


def search_multiple_levels(combinations_reverse, desired_levels, root):
    results = []

    for level in desired_levels:
        combinations = search_combinations_by_level(combinations_reverse, level)

        # Compute combinations_tags
        combinations_tags = [[root.find_tag_name_by_id(id) for id in combination] for combination in combinations]

        # Compute combinations_keys
        combinations_keys = [",".join(tags) for tags in combinations_tags]

        results.append({
            'level': str(level), 
            'combinations': combinations, 
            'combinations_tags': combinations_tags,
            'combinations_keys': combinations_keys,
            'combinations_keys_ordered': get_combinations_keys_ordered(combinations_keys, combinations)
        })

    return results