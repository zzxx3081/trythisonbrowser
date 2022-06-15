prerequsite
- docker
- fuser

docker stop $(docker ps -a -q)
docker rm $(docker ps -a -q)
docker rmi -f $(docker images -q)

docker pull registry:2
docker run -dit --name docker-registry -p 5000:5000 registry:2

# 이미지 확인하기
curl -X GET http://localhost:5000/v2/_catalog
# 출력 {"repositories":["hello-world"]}

# 태그 정보 확인하기
curl -X GET http://localhost:5000/v2/hello-world/tags/list
# 출력 {"name":"hello-world","tags":["latest"]}
