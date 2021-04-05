import re

mention_regex = re.compile("<@!([0-9]+)>")


def mention_to_id(mention):
    match = mention_regex.findall(mention)
    if len(match) == 1:
        return match[0]
    raise ValueError("Invalid user mention: {}".format(mention))
