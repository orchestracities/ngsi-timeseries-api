
def list_of_api():
    return {
	'/v2/config': 'Customize your persistance configuration to  better suit  your needs',
	'/v2/health': 'Returns the health-check status of QuantumLeap and the services it depends on',
	'/v2/notify': 'Notify QuantumLeap the arrival of a new NGSI notification.',
	'/v2/subscribe': 'Subscribe QL to process Orion notifications of certain type.',
	'/v2/entities/{entityId}/attrs/{attrName}': 'History of an attribute of a given entity instance.',
	'/v2/entities/{entityId}/attrs/{attrName}/value': 'History of an attribute (values only) of a given entity instance.',
	'/v2/entities/{entityId}': 'History of N attributes of a given entity instance.',
	'/v2/entities/{entityId}/value': 'History of N attributes (values only) of a given entity instance.',
	'/v2/types/{entityType}/attrs/{attrName}':'History of an attribute of N entities of the same type.',
	'/v2/types/{entityType}/attrs/{attrName}/value':'History of an attribute (values only) of N entities of the same type.',
	'/v2/types/{entityType}':'History of N attributes of N entities of the same type.',
	'/v2/types/{entityType}/value':'History of N attributes (values only) of N entities of the same type.',
	'/v2/attrs/{attrName}':'History of an attribute of N entities of N types.',
	'/v2/attrs/{attrName}/value':'History of an attribute (values only) of N entities of N types.',
	'/v2/attrs': ' History of N attributes of N entities of N types.',
	'/v2/attrs/value':'History of N attributes (values only) of N entities of N types.'

    }
