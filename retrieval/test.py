# from pymilvus import MilvusClient, model
# from threading import Thread

# uri = 'http://localhost:19530'
# db_name = [
#     'db_d5deedcce3ded453cfe7ce7f32b72860f4f35d6e424ba92fc5bc8cc21d2ba0c8',
#     'db_8cac3ca7475ef0c4ff13556daf9f97c850ec2ff8b2d7413baaad096177d8d602',
#     'db_69e113e25e3920bc67180f90dfe082c5116b6fe9b181f537e2f9288b08b20415',
#     'db_7848010e2c2e88fd3683191e44e39c72fc34a93ad52c3b11597e87f92b581d79',
#     'db_fcd31719bd6aba6bf1d86936c62fc9fd341803fa6d2275ae53e9a06d6a60c11f',
# ]

# clients = []
# for i in range(5):
#     clients.append(
#         MilvusClient(
#             uri = uri,
#         )
#     )

# class query_by_thread(Thread):
#     def __init__(self, client, db_name):
#         Thread.__init__(self)
#         self.client = client
#         self.db_name = db_name

#     def run(self):
#         client = self.client
#         db_name = self.db_name

#         client = MilvusClient(
#             uri = uri,
#             db_name = db_name,
#         )

#         client.load_collection(collection_name = 'types')
#         print(client.get(
#             collection_name = 'types',
#             ids = [0]
#         )[0]['data_path'])
#         client.release_collection(collection_name = 'types')

# threads = []
# for i in range(5):
#     j = query_by_thread(clients[i], db_name[i])
#     j.start()

#     threads.append(j)

# for thread in threads:
#     thread.join()

dictt = {}

dictt['key'] = [123, 12, 1, 1, 1, 1]
dictt['ket1'] = [12, 2, 2]

import time
while(len(dictt) > 0):
    for key in dictt:
        if (len(dictt[key]) > 0):
            dictt[key].pop()

    for key in list(dictt):
        if (len(dictt[key]) == 0):
            dictt.pop(key)