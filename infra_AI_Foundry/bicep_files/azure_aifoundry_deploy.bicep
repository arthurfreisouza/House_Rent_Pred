@description('The name of the person/owner for the naming convention.')
param personName string

@description('Specifies the name of the environment (e.g., dev, prod).')
param environment string

@description('Specifies the location of the resources.')
@allowed([
    'australiaeast'
    'brazilsouth'
    'canadacentral'
    'centralus'
    'eastasia'
    'eastus'
    'eastus2'
    'francecentral'
    'japaneast'
    'koreacentral'
    'northcentralus'
    'northeurope'
    'southeastasia'
    'southcentralus'
    'uksouth'
    'westcentralus'
    'westus'
    'westus2'
    'westeurope'
    'usgovvirginia'
  ])
param location string

@description('Display name for the default Foundry project.')
param projectDisplayName string = 'Default Project'

@description('Description for the default Foundry project.')
param projectDescription string = 'Default AI Foundry project'

// Naming convention: {personName}-{environment}
var baseName = toLower('${personName}-${environment}')
var foundryAccountName = take('aif-${baseName}', 64)
var foundryProjectName = take('proj-${baseName}', 64)
// customSubDomainName must be globally unique and DNS-safe
var customSubDomain = take(replace('aif-${baseName}', '_', '-'), 64)

// Azure AI Foundry account — the modern Foundry resource (GA 2025).
// Replaces the legacy Microsoft.MachineLearningServices/workspaces Hub.
resource foundryAccount 'Microsoft.CognitiveServices/accounts@2025-06-01' = {
  name: foundryAccountName
  location: location
  kind: 'AIServices'
  sku: {
    name: 'S0'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    // Required to expose this account as an AI Foundry resource with projects
    allowProjectManagement: true
    customSubDomainName: customSubDomain
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: false
    networkAcls: {
      defaultAction: 'Allow'
    }
  }
}

// Default Foundry project under the account
resource foundryProject 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' = {
  parent: foundryAccount
  name: foundryProjectName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    displayName: projectDisplayName
    description: projectDescription
  }
}

output foundryAccountName string = foundryAccount.name
output foundryProjectName string = foundryProject.name
output foundryEndpoint string = foundryAccount.properties.endpoint
