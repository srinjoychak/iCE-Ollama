# import jwt
import base64
import datetime
import json
import logging

import requests

# from decouple import config
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect
from django.utils import timezone


from pymongo import MongoClient
from rest_framework.parsers import JSONParser



bdb_uri = "https://scripts.cisco.com/api/v2/"
oauth_uri = "https://cloudsso.cisco.com"
client_id = "SSO_iCE_Test"  # config("OAUTH_CLIENT_ID", "")
# redirect_uri = "http://localhost:4200/"  # config("OAUTH_REDIRECT_URI", "")
redirect_uri = "http://10.106.32.165:4200/"
# redirect_uri = config("OAUTH_REDIRECT_URI", "")

# aws_region = config("AWS_REGION", "eu-west-1")

request_path_skip_user_details = [
    "/get_scm_link",
]


def _redirect_to_oauth():
    scope = "openid"
    response_type = "code"
    prompt = "login"
    return HttpResponseRedirect(
        f"{oauth_uri}/as/authorization.oauth2?client_id={client_id}&scope={scope}&response_type={response_type}&redirect_uri={redirect_uri}&prompt={prompt}"
    )


def _get_access_token_and_remove_auth_code_from_url(authorization_code, request):
    session = requests.session()
    client_secret = "iCETest"  # config("OAUTH_CLIENT_SECRET", "")
    try:
        response = session.post(
            f"{oauth_uri}/as/token.oauth2?code={authorization_code}&client_id={client_id}&client_secret={client_secret}&redirect_uri={redirect_uri}&grant_type=authorization_code"
        )
        response.raise_for_status()
    except requests.HTTPError:
        return _redirect_to_oauth()
    response = json.loads(response.text)
    access_token = response["access_token"]
    request.session["logadvisor_access_token"] = f"Bearer {access_token}"
    # this is to redirect without the auth code in the url
    redirect = "http://" + request.META["HTTP_HOST"] + request.META["PATH_INFO"]
    return HttpResponseRedirect(redirect)


def obssocookie_middleware(get_response):
    def validate_authentication_and_create_contributor(request, auth, obssocookie):
        session = requests.session()
        headers = {}
        if auth:
            headers = {"Authorization": auth}

        elif obssocookie:
            session.cookies.set("ObSSOCookie", obssocookie)
            headers = None

        if auth:
            if "Basic" in auth:
                # login with Bearer token or ObssoCookie
                response = session.get(f"{bdb_uri}auth/login", headers=headers)
                # checking if auth correctly
                response.raise_for_status()
                headers = None
                request.COOKIES["ObSSOCookie"] = response.cookies["ObSSOCookie"]

        # getting user id
        response = session.get(f"{bdb_uri}users/me", headers=headers)
        # if it is an request using OAuth access token, we need to ne
        response.raise_for_status()
        user_info = json.loads(response.content)

        # getting user information
        response = session.get(
            f'{bdb_uri}ldap/ccoentities/givenName,sn?filter=(uid={user_info["uid"]})',
            headers=headers,
        )
        ldapInfo = json.loads(response.content)
        user = {
            "username": user_info["uid"],
            "first_name": ldapInfo[0]["givenName"],
            "last_name": ldapInfo[0]["sn"],
            "email": f'{user_info["uid"]}@cisco.com',
        }

        # checking if the user exists in db already
        # try:

        documents = collection.find({"username": user_info["uid"]}, {"_id": 0})
        data = [document for document in documents]

        if data == []:
            collection.insert_one(user)

        else:
            update_fields = []
            # ldapInfo is empty for generic accounts
            if ldapInfo:
                if user["first_name"] != ldapInfo[0]["givenName"]:
                    update_fields.append("first_name")
                    user["first_name"] = ldapInfo[0]["givenName"]
                if user["last_name"] != ldapInfo[0]["sn"]:
                    update_fields.append("last_name")
                    user["last_name"] = ldapInfo[0]["sn"]
                if user["email"] != f'{user_info["uid"]}@cisco.com':
                    update_fields.append("email")
                    user["email"] = f'{user_info["uid"]}@cisco.com'
                if update_fields:
                    user.save(update_fields=update_fields)

        # saving the user info in the session
        request.user = user
        request.session["uid"] = user["username"]
        request.session["user_info"] = ldapInfo[0] if ldapInfo else {}

    def middleware(request):
        # skip fetching user details for specific api paths
        if any(
            path_to_skip in request.path
            for path_to_skip in request_path_skip_user_details
        ):
            response = get_response(request)
            return response
        # getting auth, cookie and auth_code
        obssocookie = request.COOKIES.get("ObSSOCookie", None)
        authorization_code = request.GET.get("code", None)
        # if auth code, then we'll have to get the access-token and remove the code auth from the url
        if authorization_code:
            return _get_access_token_and_remove_auth_code_from_url(
                authorization_code, request
            )
        # if it comes from an api
        auth = request.META.get("HTTP_AUTHORIZATION", None)
        if auth is None:
            auth = request.session.get("logadvisor_access_token", None)
        # in previous version the obssocookie was set to 'None' (str) or cookietimeout
        if obssocookie == "None" or obssocookie == "loggedoutcontinue":
            obssocookie = None
        # if internal and not authenticated, authenticate with OAuth
        xyz = request.session.get("uid")
        if auth is None and obssocookie is None:
            return _redirect_to_oauth()
        elif request.session.get("uid", None):
            try:
                # user = User.objects.get(username=request.session.get("uid"))
                user = request.session.get("uid")
            except ObjectDoesNotExist:
                try:
                    validate_authentication_and_create_contributor(
                        request=request, auth=auth, obssocookie=obssocookie
                    )
                except requests.HTTPError:
                    return _redirect_to_oauth()
            else:
                request.user = user
                if obssocookie is None and auth is None:
                    try:
                        validate_authentication_and_create_contributor(
                            request=request, auth=auth, obssocookie=obssocookie
                        )
                    except requests.HTTPError:
                        return _redirect_to_oauth()
        else:
            try:
                validate_authentication_and_create_contributor(
                    request=request, auth=auth, obssocookie=obssocookie
                )
            except requests.HTTPError:
                return _redirect_to_oauth()

        response = get_response(request)
        if request.COOKIES.get("ObSSOCookie", None) is not None and not obssocookie:
            response.set_cookie(
                key="ObSSOCookie",
                value=request.COOKIES["ObSSOCookie"],
                domain=".cisco.com",
            )
        return response

    return middleware
