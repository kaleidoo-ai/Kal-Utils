TRANSCRIPTION_REQUEST_EXAMPLE = {"id":"49","target":"orchestrator","source":"kal_sense","data":{"url": "gs://kal-sense-audio-test/audio-to transcribe/4378_CSFtoharh_42320927_0524770955_SIP_Trunk_To_ACME_42320879_0.ogg","translate_or_transcribe_task": "transcribe","language_code": "he","transcription_model": "ivrit-ai/faster-whisper-v2-d3-e3","destination":"conversations-output-data/folder_test","number_of_channel": 2,"data_flow_mode": "offline","task_id" : "123","subtask_id" : "432","org_id" : "1231","project_id" :"123"},"metadata":{"system":"pubsub","service":"orchestrator","timestamp":"2024-09-08T12:49:01.254138"}}
CREATE_TASK_EXAMPLE = {"id":"49",
                       "target":"orchestrator",
                       "source":"kal_sense",
                       "data":
                           {"product":"KalAudio",
                            "org_id":"12345a612345",
                            "project_id":"123a123a123a",
                            "path": "gs://kal-sense-audio-test/audio-to transcribe/4378_CSFtoharh_42320927_0524770955_SIP_Trunk_To_ACME_42320879_0.ogg",
                            "obj_id":"1a234561a234"},
                        "metadata":
                            {"system":"rabbitmq",
                             "service":"orchestrator",
                             "timestamp":"2024-09-08T12:49:01.254138"}}
UPDATE_TASK_EXAMPLE = {"id":"49","target":"orchestrator","source":"kal_sense","data":{},"metadata":{"system":"rabbitmq","service":"orchestrator","timestamp":"2024-09-08T12:49:01.254138"}}
