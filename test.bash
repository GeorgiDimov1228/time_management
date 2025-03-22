# Create a New User
curl -X POST \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNzQwNzU2Mzk1fQ.LrbxnKh20mJFYlGD47sfz3KxkerWN4kFWV8hSjR2k1o" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "newuser@example.com",
    "rfid": "1234567890",
    "password": "securepassword",
    "is_admin": false
  }' \
  http://localhost:8000/api/users



# Token Endpoint (Admin Login) with default
curl -X POST -H "Content-Type: application/x-www-form-urlencoded" \
-d "username=admin&password=adminpassword" \
http://localhost:8000/api/token


# List All Users
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNzQwNzU2Mzk1fQ.LrbxnKh20mJFYlGD47sfz3KxkerWN4kFWV8hSjR2k1o" http://localhost:8000/api/users

# Retrieve a Specific User
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNzQwNzU2Mzk1fQ.LrbxnKh20mJFYlGD47sfz3KxkerWN4kFWV8hSjR2k1o" http://localhost:8000/api/users/2

# Update a User
curl -X PUT -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNzQwNzU2Mzk1fQ.LrbxnKh20mJFYlGD47sfz3KxkerWN4kFWV8hSjR2k1o" -H "Content-Type: application/json" -d '{
  "username": "updateduser",
  "email": "updateduser@example.com",
  "rfid": "0987654321",
  "password": "newsecurepassword"
}' \
http://localhost:8000/api/users/1

# Delete a User
curl -X DELETE -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNzQwNzU2Mzk1fQ.LrbxnKh20mJFYlGD47sfz3KxkerWN4kFWV8hSjR2k1o" http://localhost:8000/api/users/1


# Attendance Endpoints
curl -X POST "http://localhost:8000/api/checkin?rfid=1234567890" 

# List All Check-In Events
curl http://localhost:8000/api/checkin

# Check-Out (Record an Attendance Event)
curl -X POST "http://localhost:8000/api/checkout?rfid=1234567890"


# List All Check-Out Events
curl http://localhost:8000/api/checkout
