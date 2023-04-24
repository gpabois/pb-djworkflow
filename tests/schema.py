from graphene import ObjectType, Mutation, Schema

from pb_djworkflow.schema import generate_flow_mutation
from . import flows
from . import models

SimpleFlowMutations = generate_flow_mutation(
    flows.Rvat, 
    models.Rvat
)

class Query(ObjectType):
    pass

class Mutation(Mutation, SimpleFlowMutations):
    pass

schema = Schema(query=Query, mutation=Mutation)