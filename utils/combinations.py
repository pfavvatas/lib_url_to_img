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

def search_combinations_by_length(combinations_reverse, desired_length):
    try:
        desired_length = int(desired_length)
    except ValueError:
        print("\033[91m [search_combinations_by_length] WARNING: You did not enter a valid integer. \033[0m")

    search_results = []

    for combinations_by_id, data in combinations_reverse.items():
        found_match = False

        for sub_comb, length in data['combinations_by_id']:
            if length == desired_length:
                search_results.append((sub_comb))
                found_match = True
                break

        if not found_match:
            for sub_comb, length in data['combinations_by_id']:
                if length < desired_length:
                    search_results.append((sub_comb))
                    found_match = True
                    break

        if not found_match:
            for sub_comb, length in reversed(data['combinations_by_id']):
                if length > desired_length:
                    continue
                if length <= desired_length:
                    search_results.append((sub_comb))
                    found_match = True
                    break

    return search_results

def search_multiple_lengths(combinations_reverse, desired_lengths):
    results = []

    for length in desired_lengths:
        combinations = search_combinations_by_length(combinations_reverse, length)
        results.append({'level': str(length), 'combinations': combinations})

    return results