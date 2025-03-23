def config_record(data):
    for i in range(len(data)):
        data[i]['deleted'] = False
    return data