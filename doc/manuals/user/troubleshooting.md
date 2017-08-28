# Troubleshooting

Something not working as expected? Don't worry! the expected thing is for it not to work :p.

Checkout the following section to make sure you didn't miss a critical step, and if none of that applies to your case, then refer to the **Bug Reporting** section.


## Nothing Happens

If you don't see your data being saved in the database, before reporting a bug please ask yourself the following questions:

- Have you created a subscription for the entity type you are inserting?

- Are you inserting/updating attributes listed in the "condition" of the subscription? I.e, will Orion trigger notifications for that insert/update?

- Is the location of QuantumLeap expressed in the *notify_url* field of the subscription a resolvable url for the conteinerized Orion? Review the [Usage Section](./index.md) for more details.

- Are you running the different components behind firewalls? If so, did you open the corresponding ports? (See the [Ports](../admin/ports.md) section.)


## Bug reporting

Bugs should be reported in the form of [issues](https://github.com/smartsdk/ngsi-timeseries-api/issues) in the github repository.

Please, look through the open issues before opening a repeated one :)

Include as much context info as possible, also ideally the following things:

- The inserted entity that may have caused the problem. E.g:

        {
            'id': 'Room1',
            'type': 'Room',
            'attr1': 'blabla',
            ...
        }

- The payload of the subscription(s) that you created.
- The logs of the QuantumLeap container.

    The logs can be retrieved with the *[docker logs command](https://docs.docker.com/engine/reference/commandline/logs/#options)* or *[docker service logs](https://docs.docker.com/engine/reference/commandline/service_logs/)* if you deployed QL as a service on Swarm. In the first case, you can discover the container id with *[docker ps -a]()*.
