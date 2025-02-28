# Create a New User

curl -X POST -H "Content-Type: application/json" \
-d '{
  "username": "newuser",
  "email": "newuser@example.com",
  "rfid": "1234567890",
  "password": "securepassword",
  "is_admin": "true"
}' \
http://localhost:8000/api/users



# Token Endpoint (Admin Login) with default

curl -X POST -H "Content-Type: application/x-www-form-urlencoded" \
-d "username=admin&password=adminpassword" \
http://localhost:8000/api/token


# List All Users

curl http://localhost:8000/api/users


curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNzQwNzA2NDYyfQ.x9ekc9JJG-lTByEkIKLlXyQ2bkfalnTVaB9dMaZ7oK8" \
http://localhost:8000/api/users

# Retrieve a Specific User

curl http://localhost:8000/api/users/1

# d. Update a User

curl -X PUT -H "Content-Type: application/json" \
-d '{
  "username": "updateduser",
  "email": "updateduser@example.com",
  "rfid": "0987654321",
  "password": "newsecurepassword"
}' \
http://localhost:8000/api/users/1

#e. Delete a User

curl -X DELETE http://localhost:8000/api/users/1


# 3. Attendance Endpoints

curl -X POST "http://localhost:8000/api/checkin?rfid=1234567890" 

# . List All Check-In Events

curl http://localhost:8000/api/checkin

# c. Check-Out (Record an Attendance Event)

curl -X POST "http://localhost:8000/api/checkout?rfid=1234567890"


# d. List All Check-Out Events

curl http://localhost:8000/api/checkout
