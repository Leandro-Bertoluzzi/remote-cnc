def serializeList(listToSerialize):
    """Return object list in an easily serializable format"""
    return [item.serialize() for item in listToSerialize]
