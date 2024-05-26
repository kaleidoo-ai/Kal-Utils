from fastapi import status

def return_response(res=None, error=None, data=False):
    if error:
        return {"message": f"Internal Server Error: {error}", "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}
    if res:
        response_status = res.get("status")
        del res["status"]
        if response_status == "success":
            res["status_code"] = status.HTTP_200_OK
            return res
        if data:
            res["status_code"] = status.HTTP_404_NOT_FOUND
            return res
        res["status_code"] = status.HTTP_400_BAD_REQUEST
        return res
