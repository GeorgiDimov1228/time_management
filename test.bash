


# Token Endpoint (Admin Login) with default
curl -X POST -H "Content-Type: application/x-www-form-urlencoded" \
-d "username=admin&password=adminpassword" \
http://localhost:8000/api/token | json_pp

# Get token and save it to a variable
export TOKEN=$(curl -s -X POST -H "Content-Type: application/x-www-form-urlencoded" \
-d "username=admin&password=adminpassword" \
http://localhost:8000/api/token | grep -o '"access_token":"[^"]*' | sed 's/"access_token":"//')

# Verify token was captured
echo $TOKEN

# Create a New User
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "bridge",
    "email": "bridge@example.com",
    "rfid": "bridgerfid",
    "password": "bridgepassword",
    "is_admin": false
  }' \
  http://localhost:8000/api/users | json_pp

  curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "listener",
    "email": "listener@example.com",
    "rfid": "listenerrfid",
    "password": "listenerpassword",
    "is_admin": false
  }' \
  http://localhost:8000/api/users | json_pp

# List All Users
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/users | json_pp

# Retrieve a Specific User
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/users/5 | json_pp

# Update a User

curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "updateduser",
    "email": "updateduser@example.com",
    "rfid": "0987654321",
    "password": "newsecurepassword",
    "is_admin": false
  }' \
  http://localhost:8000/api/users | json_pp

curl -X PUT -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{
  "username": "updateduser",
  "email": "updateduser@example.com",
  "rfid": "0987654321",
  "password": "newsecurepassword"
}' \
http://localhost:8000/api/users/5 | json_pp


# Update a User's Password
curl -X PUT \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "newsecurepassword",
    "new_password": "securepassword"
  }' \
  http://localhost:8000/api/users/5/password | json_pp

  # Update a User's Password
curl -X PUT \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "securepassword",
    "new_password": "newsecurepassword"
  }' \
  http://localhost:8000/api/users/5/password | json_pp



# Attendance Endpoints
curl -X POST -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/checkin?rfid=0987654321"  | json_pp
curl -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/employees/status?rfid=0987654321" | json_pp

# Check-Out (Record an Attendance Event)
curl -X POST -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/checkout?rfid=0987654321" | json_pp
curl -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/employees/status?rfid=828AFB03" | json_pp

# List All Check-In Events
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/checkin | json_pp
# List All Check-Out Events
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/checkout | json_pp


# Delete a User
curl -X DELETE -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/users/5 | json_pp


curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" -d '{"rfid": "123456789"}' http://localhost:8000/api/scan