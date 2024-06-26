# setup
- u have to run docker in this folder first with `docker compose up -d`
- next run `docker cp milvus.yaml <milvus_container_id>:/milvus/configs/milvus.yaml` to copy the config file for milvus to the container
- next run `docker stop <milvus_container_id>` and `docker start <milvus_container_id>` to restart