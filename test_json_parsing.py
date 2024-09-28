import json

# Gantilah string JSON di bawah ini dengan nilai FIREBASE_CONFIG Anda
firebase_config = '''{
  "type": "service_account",
  "project_id": "amimumherbalproject-427e5",
  "private_key_id": "1106f1aef571781e414512c37c298994b7cfb421",
  "private_key": "-----BEGIN PRIVATE KEY-----\\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCP5yAItk6u6hhh\\npEqzmJYYju7x0VMwNxqFuC0G0rf98bU7r0p5JEL8AgW/rKDJpDo20+UGYXc301vz\\nJZZBK9PKgfmWCDyCTI3iJnT3bO6dIKdfQBD2uhslksmpALRWPmS0PR4HLnWIai1d\\nZkZixaFEUhKkH83kPfSV4g+uqLVU55cIZWr/ay0T2KQFLmWaSsFPr6cBXpoOpwGB\\n+qVhe7E7vk94IS7EhcMBzY/zjcg6UqRTxdcppypEFa4SAcOLW3TyhjYS54Kiq1A/\\nO1vyRqY9Z17Qa6QqcoDIobm4F4m44JoPg63n0qUwfjub1h5yyvM0Q8YmS8tAA714\\ncyDyr8CpAgMBAAECggEAAmBdmn4V9Ws81PtlBP2u87soi5gRXVcLnsv8+4NKxEf4\\ncIK+2T8DfCzHzc8a3TmcgRIlm8+nGYF8DYkJXsNLqvIvHiDiaBIrk2GoWESMQxdz\\nh5KWIthf84kuv/F0LYYlrwaX7hHcDwgWbEWVQbMtPpuXzFvH0GCMaFZkhQy9VnGW\\nTAYFwE0c0FzwZ8i7ptsVTVJvrwj9gibWXMbigaiU+kf8UmV+SusD3mRh2xW5/Lv/\\nwqSfEGfepgCIACGXbnjlzZlbxWOxGEK//C5AH+EqXBmDruhqIVttVJL66EZ5RlZk\\nBQm2zWVQTtdOgTh23UtanqAVDnoD3yDC5BfvyrK8oQKBgQDJxTBzRiKTV7KYd37F\\nWLUDZ8MRigXM1xEzmzurFuHn2LXXc4fDija429yZLhAyk/cPuJu4oY500NFQ3e/P\\n9PDKBS8chZ7+f0HAAdRpe3SwngLcTqBsdiy4iNYpZ/rzGK2FK0vQvlGUn3ds1egU\\nuM1wMoUD0ORMA/+1TiWlw6xCMwKBgQC2lF1eCJ+Eb4BsS3T2ln8h1Mr15TXvndKB\\noAfdghkpwdNGQUOP5R3bUazIZrRXtBSApxqTvvRwNY5dllzvhH9IV8b2KjM/nx+0\\nt3eABG/Xc8O3ZCt6mLx+/X3VBF0ZrYZTVkqwf5NzEHEiLfq5KJHxGj8azRvKYqh0\\nOqoYbnutswKBgG6hfkVWaVLcvQI4Uvwl/WpWlHCjezarnbTsIrVWoJsdCeeOYxxm\\nRkbp1nTu+tagptCp6kg73P5UGND8P6eIqBY87W34Hgtw/z4mQq9rj7nfibX+LpwJ\\n189+x96AMurj1xCzgqh8EgMpxLOaPdxOz+X67VAAU40SjDx/EslnFqZdAoGAUJIu\\nlcWmZ3IxMRknd344gjx+iH7rC2AROmTds7Gq2xOO4a0BXKnWQCfN4O353c45UgDs\\nKJEXG8F2nvQw9P36kXky8wTycrwM6Noh4RuUI3cRwodw7HwkisHg2rU/RIqgAXzO\\nHw9diWSTGGtD/pvZs5VKjdA/2FMrVYdh8sAm0iMCgYEAh8/ZDLz9+3cntbndZEUK\\nwzl8CV7YSNAdKWJqkmDLARMfaiegva4KRik38e3b3YAiis7LSh86h0kqAT+qheg4\\nklP6vFCrXwyR1uKAKXKeCXkGuRD0wpKVeAYd1BlLF6YSh6eCKzt5ld868OVX9L5M\\ni0XIJ1MwKqAZIGFtJ1xpbiE=\\n-----END PRIVATE KEY-----\\n",
  "client_email": "firebase-adminsdk-rrw6t@amimumherbalproject-427e5.iam.gserviceaccount.com",
  "client_id": "100957031538253987965",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-rrw6t%40amimumherbalproject-427e5.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}'''

try:
    # Mencoba untuk menguraikan JSON
    config_dict = json.loads(firebase_config)
    print("Parsed FIREBASE_CONFIG:", config_dict)
except json.JSONDecodeError as e:
    print("JSON Decode Error:", e)
