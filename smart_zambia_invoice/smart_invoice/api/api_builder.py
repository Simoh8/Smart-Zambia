from __future__ import annotations
from typing import Literal,Callable
from urllib import parse
import aiohttp.client_exceptions
from  frappe.integrations.utils import create_request_log
from frappe.model.document import Document

import asyncio
import aiohttp

import frappe
from frappe.model.document import Document
from ..utilities import make_post_request
from ..zra_logger import zra_vsdc_logger


class BaseEndpointConstructor:


    def __init__(self) -> None:
        self.integration_requets:str | Document | None= None
        self.error: str |Exception | None=None
        self._observers: list[ErrorsObserver] =[]
        self.doctype:str | Document | None=None
        self.document_name:str | None= None



    def attach_observer(self, observer:ErrorsObserver) -> None:

        self._observers.append(observer)


    def notifty_observer(self) -> None:

        for observer in self._observers:
            observer.update(self)



class ErrorsObserver:

     def update(self, notifier: BaseEndpointConstructor) -> None:
         

         if notifier.error:
             update_integration_request(
                notifier.integration_requets.name,
                status= "Failed",
                error=notifier.error,
                output= None,
             )
             zra_vsdc_logger.exception(notifier.error, exc_info=True)

             frappe.log_error(
                title="Critical Error",
                message= notifier.error,
                reference_doctype=notifier.doctype,
                reference_name=notifier.document_name
             )
             frappe.throw(
                notifier.error,
                title="Critical Error"
             )

#  TODO     
class EndpointConstructor(BaseEndpointConstructor):


    def __init__(self) -> None:
        super().__init__()



        self._url:str |None =None
        self._payoad:dict |None =None
        self._headers: dict |None=None
        self._success_callback_handler: Callable | None= None
        self._error_callback_handler: Callable | None= None


        self.attach_observer(ErrorsObserver())

    @ property
    def url(self) -> str | None:


            return self._url

    @url.setter
    def url(self, new_url:str )-> None:

            self._url =new_url


    @property
    def payload(self)-> dict |None:

            return self._payload


    @payload.setter
    def payload(self, new_payload:dict )-> None:

            self._payload=new_payload

    @property
    def headers(self) -> dict |None:

            return self._headers


    @headers.setter
    def headers(self, new_headers:dict)-> None:

            self._headers =new_headers

    @property
    def success_callback(self) -> Callable |None:
            return self._success_callback_handler


    @success_callback.setter
    def success_callback(self,callback: Callable) -> None:
            self._succesfull_callback_handler =callback


    @property
    def error_callback(self) -> Callable |None:

        return self._error_callback_handler

    @error_callback.setter
    def error_callback(self, callback: Callable[[dict[str, str | int |None] | str, str, str, str ], None],) -> None:
        self._error_calback_handler =callback

    def perform_remote_calls(self, doctype: Document |str |None =None, document_name: str |None =None) -> None:


        if(self.url is None or self._headers is None or self._success_calback_handler is None or self._error_callback_handler is None
        ):
            frappe.throw(
                frappe.MandatoryError,

                title= "Critical Setup Error",
                is_minimizable=True
            )

        self.doctype, self.document_name= doctype, document_name
        parsed_url =parse.urlparse(self._url)
        route_path = f"/{parsed_url.path.split('/')[-1]}"

        self.interation_request = create_request_log(
        data=self._payload,
        is_remote_request= True,
        service_name="vscd",
        request_headers=self._headers,
        url= self._url,
        reference_docname=document_name,
        reference_doctype=doctype,
        )

        try:
            response =asyncio.run( make_post_request(self._url, self._payload, self._headers))

            if response["resultCd"]== "000":
                
                self._success_callback_handler(response)

                # update_last_request_dates(response["resultDt"], route_path)

                update_integration_request(self.intergration_request_name.name, status= "Completed" ,output=response["resultMsg"], error=None,)

            else:
                update_integration_request(
                    self.intergration_request.name,
                    status="Failed",
                    output=response["resultMsg"],
                    error=None,
                )

                self._enotifyrror_callback_handler(
                    response,
                    url=route_path,
                    doctype=doctype,
                    document_name=document_name
                )
        except (

                aiohttp.client_exceptions.ClientConnectionError,
                aiohttp.client_exceptions.ClientOSError,
                asyncio.exceptions.TimeoutError,   
        ) as error:
                self.error=error,
                self.notify_observer()

def update_integration_request(integration_request: str,status:Literal["Completed", "Failed"],output:str |None =None,error:str |None=None,) -> None:

    doc = frappe.get_doc("Integration Request", integration_request, for_update=True)
    doc.status = status
    doc.error = error
    doc.output = output

    doc.save(ignore_permissions=True)


