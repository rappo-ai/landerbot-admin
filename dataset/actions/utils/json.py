def get_json_key(dict, key, default=None):
    try:
        key_split = key.split(".", 1)
        key_split_len = len(key_split)
        if key_split_len == 2:
            return get_json_key(dict[key_split[0]], key_split[1], default)
        elif key_split_len == 1:
            return dict[key_split[0]]
    except:
        return default
    return default
