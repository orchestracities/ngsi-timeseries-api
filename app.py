from utils.hosts import LOCAL


if __name__ == '__main__':
    import connexion
    app = connexion.FlaskApp(__name__, specification_dir='specification/')
    app.add_api('quantumleap.yml', arguments={'title': 'QuantumLeap V2 API'},
                # validate_responses=True, strict_validation=True
                )
    app.run(host=LOCAL, port=8668)
