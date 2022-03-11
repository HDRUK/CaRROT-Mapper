import React, { useState, useEffect, useRef } from 'react'
import {
    Select, Box, Text, Button, Flex, Spinner, Container, Input, Tooltip, CloseButton, ScaleFade, useDisclosure, Switch,
    FormControl, FormLabel, FormErrorMessage
} from "@chakra-ui/react"
import PageHeading from './PageHeading'
import ToastAlert from './ToastAlert'
import ConceptTag from './ConceptTag'
import { useGet, usePatch, useDelete } from '../api/values'

const DatasetAdminForm = ({ setTitle }) => {
    let datasetId = window.location.pathname.split("/").pop()
    const { isOpen, onOpen, onClose } = useDisclosure()

    // Set up component state
    const [alert, setAlert] = useState({ hidden: true, title: '', description: '', status: 'error' })
    const [dataset, setDataset] = useState({})
    const [dataPartners, setDataPartners] = useState();
    const [selectedDataPartner, setSelectedDataPartner] = useState()
    const [isPublic, setIsPublic] = useState()
    const [loadingMessage, setLoadingMessage] = useState("Loading page")
    const [formErrors, setFormErrors] = useState({})
    const [uploadLoading, setUploadLoading] = useState(false)
    const [viewers, setViewers] = useState([])
    const [admins, setAdmins] = useState([])
    const [usersList, setUsersList] = useState(undefined)

    function getUsersFromIds(userIds, userObjects) {
        /**
         * Get an array user objects with ids in an array of ids.
         * 
         * userIds: Array[Number]
         * userObjects: Array[Object]
         */
        const idIterator = userIds.values()
        let users = []
        for (let id of idIterator) {
            for (let obj of userObjects) {
                if (id === obj.id) {
                    users.push(obj)
                }
            }
        }
        return users
    }

    // Set up page
    useEffect(
        async () => {
            setTitle(null)
            const queries = [
                useGet(`/datasets/${datasetId}`),
                useGet("/datapartners/"),
                useGet("/users/"),
            ]
            // Get dataset, data partners and users
            const [datasetQuery, dataPartnerQuery, usersQuery] = await Promise.all(queries)
            // Set up state from the results of the queries
            setDataset(datasetQuery)
            setIsPublic(datasetQuery.visibility === "PUBLIC")
            setDataPartners([...dataPartnerQuery])
            setSelectedDataPartner(
                dataPartnerQuery.find(element => element.id === datasetQuery.data_partner)
            )
            setLoadingMessage(null)
            setUsersList(usersQuery)
            setViewers(
                prevViewers => [
                    ...prevViewers,
                    ...getUsersFromIds(datasetQuery.viewers, usersQuery),
                ]
            )
            setAdmins(
                prevAdmins => [
                    ...prevAdmins,
                    ...getUsersFromIds(datasetQuery.admins, usersQuery),
                ]
            )
            setLoadingMessage(null)  // stop loading when finished
        },
        [], // Required to stop this effect sending infinite requests
    )

    useEffect(
        async () => {
            setFormErrors({ ...formErrors, name: undefined })
        },
        [dataset.name],
    )

    useEffect(
        async () => {
            setFormErrors({ ...formErrors, data_partner: undefined })
        },
        [selectedDataPartner],
    )

    // Update dataset name
    function handleNameInput(newValue) {
        setDataset({ ...dataset, name: newValue })
    }

    // Update dataset visibility
    function handleVisibilitySwitch(newValue) {
        setIsPublic(newValue)
        setDataset({ ...dataset, visibility: newValue ? "PUBLIC" : "RESTRICTED" })
    }

    // Update dataset data partner
    function handleDataPartnerSelect(newValue) {
        const dataPartner = JSON.parse(newValue)
        setSelectedDataPartner(dataPartner)
        setDataset({ ...dataset, data_partner: dataPartner.id })
    }

    // Remove user chip from viewers
    const removeViewer = (id) => {
        setViewers(pj => pj.filter(user => user.id != id))
    }

    // Remove user chip from viewers
    const removeAdmin = (id) => {
        setAdmins(pj => pj.filter(user => user.id != id))
    }

    // Send updated dataset to the DB
    async function upload() {
        /**
         * Send a `PATCH` request updating the dataset and
         * refresh the page with the new data
         */
        try {
            setUploadLoading(true)
            const response = await usePatch(
                `/datasets/update/${datasetId}`,
                {
                    ...dataset,
                    data_partner: selectedDataPartner.id,
                    viewers: [...viewers.map(viewer => viewer.id)],
                    admins: [...admins.map(admin => admin.id)],
                },
            )
            setUploadLoading(false)
            setDataset(response)
            setAlert({
                hidden: false,
                status: 'success',
                title: 'Success',
                description: 'Dataset updated'
            })
            onOpen()
        } catch (error) {
            const error_response = await error.json()
            setUploadLoading(false)
            if (error_response) {
                setFormErrors(error_response)
            }
            setAlert({
                hidden: false,
                status: 'error',
                title: 'Could not update dataset',
                description: error.statusText ? error.statusText : ""
            })
            onOpen()
        }
    }


    if (loadingMessage) {
        //Render Loading State
        return (
            <div>
                <Flex padding="30px">
                    <Spinner />
                    <Flex marginLeft="10px">{loadingMessage ? loadingMessage : "Loading page"}</Flex>
                </Flex>
            </div>
        )
    }

    return (
        <Container maxW='container.xl'>
            {isOpen &&
                <ScaleFade initialScale={0.9} in={isOpen}>
                    <ToastAlert hide={onClose} title={alert.title} status={alert.status} description={alert.description} />
                </ScaleFade>
            }

            <PageHeading text={`Admin Page for Dataset #${dataset.id}`} />

            <FormControl mt={4} isInvalid={formErrors.name && formErrors.name.length > 0}>
                <FormLabel htmlFor="dataset-name" style={{ fontWeight: "bold" }}>Name:</FormLabel>
                <Input
                    id="dataset-name"
                    value={dataset.name}
                    onChange={e => handleNameInput(e.target.value)}
                />
                {formErrors.name && formErrors.name.length > 0 &&
                    <FormErrorMessage>{formErrors.name[0]}</FormErrorMessage>
                }
            </FormControl>
            <FormControl mt={4}>
                <FormLabel htmlFor="dataset-visibility" style={{ fontWeight: "bold" }}>Visibility:</FormLabel>
                <Flex alignItems={"center"}>
                    <Switch
                        id="dataset-visibility"
                        isChecked={isPublic}
                        onChange={e => handleVisibilitySwitch(!isPublic)}
                    />
                    <Text fontWeight={"bold"} ml={2}>{dataset.visibility}</Text>
                </Flex>
            </FormControl>
            {!isPublic &&
                <>
                    <Box mt={4}>
                        <div style={{ display: "flex", flexWrap: "wrap", marginTop: "10px" }}>
                            <div style={{ fontWeight: "bold", marginRight: "10px" }} >Viewers: </div>
                            {viewers.map((viewer, index) => {
                                return (
                                    <div key={index} style={{ marginTop: "0px" }}>
                                        <ConceptTag conceptName={viewer.username} conceptId={""} conceptIdentifier={viewer.id} itemId={viewer.id} handleDelete={removeViewer} />
                                    </div>
                                )
                            })}
                        </div>
                        {usersList == undefined ?
                            <Select isDisabled={true} icon={<Spinner />} placeholder='Loading Viewers' />
                            :
                            <Select bg="white" mt={4} value="Add Viewer" readOnly onChange={(option) => setViewers(pj => [...pj.filter(user => user.id != JSON.parse(option.target.value).id), JSON.parse(option.target.value)])}>
                                <option disabled>Add Viewer</option>
                                <>
                                    {usersList.map((item, index) =>
                                        <option key={index} value={JSON.stringify(item)}>{item.username}</option>
                                    )}
                                </>
                            </Select>
                        }
                    </Box>
                </>
            }
            <FormControl mt={4}>
                <FormLabel htmlFor="dataset-datapartner" style={{ fontWeight: "bold" }}>Data Partner:</FormLabel>
                <Select
                    id="dataset-datapartner"
                    value={JSON.stringify(selectedDataPartner)}
                    onChange={(option) => handleDataPartnerSelect(option.target.value)}
                >
                    {dataPartners.map((item, index) =>
                        <option key={index} value={JSON.stringify(item)}>{item.name}</option>
                    )}
                </Select>
            </FormControl>
            <Box mt={4}>
                <div style={{ display: "flex", flexWrap: "wrap", marginTop: "10px" }}>
                    <div style={{ fontWeight: "bold", marginRight: "10px" }} >Admins: </div>
                    {admins.map((viewer, index) => {
                        return (
                            <div key={index} style={{ marginTop: "0px" }}>
                                <ConceptTag conceptName={viewer.username} conceptId={""} conceptIdentifier={viewer.id} itemId={viewer.id} handleDelete={removeAdmin} />
                            </div>
                        )
                    })}
                </div>
                {usersList == undefined ?
                    <Select isDisabled={true} icon={<Spinner />} placeholder='Loading Viewers' />
                    :
                    <Select bg="white" mt={4} value="Add Admin" readOnly onChange={(option) => setAdmins(pj => [...pj.filter(user => user.id != JSON.parse(option.target.value).id), JSON.parse(option.target.value)])}>
                        <option disabled>Add Admin</option>
                        <>
                            {usersList.map((item, index) =>
                                <option key={index} value={JSON.stringify(item)}>{item.username}</option>
                            )}
                        </>
                    </Select>
                }
            </Box>

            <Button isLoading={uploadLoading} loadingText='Uploading' mt="10px" onClick={upload}>Submit</Button>
        </Container>
    )
}

export default DatasetAdminForm