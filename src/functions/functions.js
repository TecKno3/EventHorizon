import store from '@/store'
import api from '@/functions/apiFunctions.js'
export default {
    get currentPage() {
        return store.pages[store.pages.length - 1]
    },
    get previousPage() {
        return store.pages[store.pages.length - 2]
    },
    get currentUrl() {
        let result = window.origin + '/?page=' + this.currentPage.page
        let argKeys = Object.keys(this.currentPage.args)
        for (let i = 0; i < argKeys.length; i++) {
            result += '&' + argKeys[i] + '=' + this.currentPage.args[argKeys[i]]
        }
        return result
    },
    get isAuthenticatedUser() {
        let result = this.inGroups(['User', 'Admin'])
        return result
    },
    get isAdmin() {
        let result = this.inGroups(['Admin'])
        return result
    },
    get today() {
        return new Date()
    },
    get queryFromUrl() {
        let urlSearchParams = new URLSearchParams(window.location.search)
        return Object.fromEntries(urlSearchParams.entries())
    },
    inGroups(groupNames) {
        let groupIds = []
        for (let i = 0; i < groupNames.length; i++) {
            groupIds.push(store.groups.filter(group => {
                if (group.name === groupNames[i]) {
                    return true
                } else {
                    return false
                }
            })[0].id)
        }
        let result = groupIds.includes(store.user.groups[0])
        return result
    },
    createUrl(pageDict) {
        let result = window.origin + '/?page=' + pageDict.page
        let argKeys = Object.keys(pageDict.args)
        for (let i = 0; i < argKeys.length; i++) {
            result += '&' + argKeys[i] + '=' + pageDict.args[argKeys[i]]
        }
        return result
    },
    goToPage(pageDict) {
        store.pages.push(pageDict)
        if (!['loginRegister', 'registerWithEmail', 'forgotPassword', 'resetPassword'].includes(pageDict.page)) {
            store.lastNonLoginRegisterPage = pageDict
        }
    },
    goBack() {
        if (store.pages.length === 1) {
            window.history.go(-2)
        } else {
            store.pages.pop() // remove the current page
        }
    },
    focusCursor(documentt, id) {
        setTimeout(() => { documentt.getElementById(id).focus() }, 200)
    },
    isGuestStatus(event, guestStatus) {
        if (Array.isArray(event[guestStatus])) {
            return event[guestStatus].includes(store.user.id)
        } else {
            return false
        }
    },
    async getEvents() {
        let events = await api.getAllEvents()
        for (let i = 0; i < events.length; i++) {
            if (events[i].images.length > 0) {
                let result = await api.getEventImage(events[i].images[0], events[i].id)
                if (result != 'fail') {
                    events[i].image_data = "data:image/jpg;base64," + result
                }
            }
        }
        store.events.all = this.sortEventsByDate(events)
        store.events.mine = this.filterEvents(store.events.all, store.user.id, ['invited'], false)
        store.events.display = store.events.all
    },
    sortEventsByDate(events) {
        let sorted_events = []
        if (events.length > 0) {
            sorted_events = events.sort((a, b) => {
                let a_date = new Date(a.date_time)
                let b_date = new Date(b.date_time)
                if (a_date.getTime() > b_date.getTime()) {
                    return 1
                } else if (a_date.getTime() < b_date.getTime()) {
                    return -1
                } else {
                    return 0
                }
            })
        }
        return sorted_events
    },
    filterEvents(events, search, criteria, strictlyEqual = false) {
        let filtered_events = []
        if (events.length > 0) {
            filtered_events = events.filter(event => {
                for (let i = 0; i < criteria.length; i++) {
                    if (!strictlyEqual) {
                        if (String(event[criteria[i]]).includes(String(search))) {
                            return true
                        }
                    } else {
                        if (String(event[criteria[i]]) === String(search)) {
                            return true
                        }
                    }
                }
                return false
            })
        }
        return filtered_events
    },
    isoStringDateToDateObject(date) {
        let b = date.split(/\D+/)
        return new Date(Date.UTC(b[0], --b[1], b[2], b[3], b[4], b[5], b[6]));
    },
    getEventWithClosestFutureDate(events, dateTime) {
        let event = []
        events = this.sortEventsByDate(events)
        if (events.length > 0) {
            event = events.filter(event => {
                let eventDate = this.isoStringDateToDateObject(event['date_time'])
                return eventDate >= dateTime
            })
            return event[0]
        }
        return event
    },
    hasIllegalSymbols(value) {
        let symbols = '`~!#$%^&*()=[{]}\\|;:\'",<>/?'
        for (let i = 0; i < symbols.length; i++) {
            if (value.includes(symbols[i])) {
                return true
            }
        }
        return false
    },
    createEncodedURL() {
        let url = 'https%3A%2F%2Fwww.eventhorizon.vip'
        if (process.env.PYTHON_ENV == 'development') {
            url = 'http%3A%2F%2F127.0.0.1%3A8080'
        } else if (process.env.PYTHON_ENV == '"test"') {
            url = 'https%3A%2F%2Fevent-horizon-test.herokuapp.com'
        }
        return url
    },
    createUriForReturnFromLogin(currentPageDict, returnToPageDict, encode) {
        let e = {
            '/': '%2F',
            '?': '%3F',
            '=': '%3D',
            '&': '%26',
        }
        let uri = null
        let argKeys = Object.keys(returnToPageDict.args)
        if (encode) {
            uri = `${e['/']}${e['?']}page${e['=']}${currentPageDict.page}${e['&']}next`
            uri += `${e['=']}${returnToPageDict.page}`
        } else {
            uri = `/?page=${currentPageDict.page}&next=${returnToPageDict.page}`
        }
        if (argKeys.length > 0) {
            for (let i = 0; i < argKeys.length; i++) {
                if (['code', 'friendship_status_changed', 'state'].includes(argKeys[i])) {
                    continue
                }
                if (encode) {
                    uri += `${e['&']}${argKeys[i]}${e['=']}${returnToPageDict.args[argKeys[i]]}`
                } else {
                    uri += `&${argKeys[i]}=${returnToPageDict.args[argKeys[i]]}`
                }
            }
        }
        return uri
    },
    createNextPageFromCurrentPage() {
        let nextArgKeys = Object.keys(this.currentPage.args)
        let nextPage = this.currentPage.args.next
        let nextArgs = {}
        if (nextArgKeys.length > 0) {
            for (let i = 0; i < nextArgKeys.length; i++) {
                if (['next', 'code', 'friendship_status_changed', 'state'].includes(nextArgKeys[i])) {
                    continue
                } else {
                    nextArgs[nextArgKeys[i]] = this.currentPage.args[nextArgKeys[i]]
                }
            }
        }
        return { page: nextPage, args: nextArgs }
    },
    createUrlForPasswordChange(email) {
        let nextArgKeys = Object.keys(store.lastNonLoginRegisterPage.args)
        let returnUrl = `${window.origin}/?page=resetPassword&next=${store.lastNonLoginRegisterPage.page}`
        returnUrl += `&email=${encodeURIComponent(email)}`
        if (nextArgKeys.length > 0) {
            for (let i = 0; i < nextArgKeys.length; i++) {
                returnUrl += `&${nextArgKeys[i]}=${store.lastNonLoginRegisterPage.args[nextArgKeys[i]]}`
            }
        }
        return returnUrl
    },
    shakeFunction(thiss) {
        if (Array.isArray(thiss)) {
            for (let i = 0; i < thiss.length; i++) {
                thiss[i].shakeIt = true
                setTimeout(() => { thiss[i].shakeIt = false; }, 1000)
            }
        } else {
            thiss.shakeIt = true
            setTimeout(() => { thiss.shakeIt = false; }, 1000)
        }
    },
}