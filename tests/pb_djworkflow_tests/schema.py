from graphene import ObjectType, Mutation, Schema
from graphene_django import DjangoObjectType
from pb_djworkflow.schema import generate_flow_mutation

from . import flows
from . import models

class SimpleContext(DjangoObjectType):
    class Meta:
        model = models.SimpleContext   

SimpleFlowMutations = generate_flow_mutation(
    flows.SimpleFlow, 
    SimpleContext
)

class Query(ObjectType):
    pass

class Mutation(SimpleFlowMutations):
    pass

schema = Schema(query=Query, mutation=Mutation)