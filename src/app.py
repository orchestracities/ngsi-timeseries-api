import connexion
app = connexion.FlaskApp(__name__, port=8668, specification_dir='../specification/')
app.add_api('quantumleap.yml',
                arguments={'title': 'QuantumLeap V2 API'},
                pythonic_params=True,
                # validate_responses=True, strict_validation=True
                )
application = app.app
