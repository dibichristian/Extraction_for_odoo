from flask import current_app, send_from_directory
import os 



class ToolController:

    def response_function(self, statut, message, resultat):
        if statut == 0:
            return{
                'Type' : 'Error',
                'Message': message,
                'Response': resultat
            }
        elif statut == 1:
            return{
                'Type' : 'Succes',
                'Response': resultat
            }
        else:
            return{
                'Type' : 'Error',
                'Response': 'Reponse non prise en charge'
            }