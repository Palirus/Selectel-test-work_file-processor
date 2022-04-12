from config import Config
import dataconf


# postgres_conf = dataconf.file('config.hocon', Config)


# async def main():
#     conf = dataconf.file('config.hocon', Config)
#     conninfo = make_conninfo(**conf.postgresql.__dict__)
#     # print(conninfo_to_dict(conninfo))

#     # test({'host': 'ff', 'password': 'ds', 'user': 'dsd', 'database': 'data'})
#     # test(conf.postgresql)
#     # host=storage, database=storage, user=user, password=password

#     db = Storage(conninfo)
#     await db.ping()


# if __name__ == "__main__":
#     asyncio.run(main())