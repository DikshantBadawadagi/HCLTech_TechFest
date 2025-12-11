For starting - docker compose up
testing - python .\backend\test_with_context.py mentorTest3.mp4 "OOPs concepts well explained using real life example"

Parallel Chunking -
POST  - http://localhost:8000/api/v1/batch/analyze-batch
FormData - 
    key = files, value = mp4,
    key = files, value = mp4,
    ...
    key = context, value = optional context