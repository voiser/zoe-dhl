#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# This file is part of Zoe Assistant - https://github.com/guluc3m/gul-zoe
#
# Copyright (c) 2014 David Muñoz Díaz <david@gul.es> 
#
# This file is distributed under the MIT LICENSE
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import zoe
from zoe.deco import *
import http.client
import xml.dom.minidom
    
CATEGORY = "dhl"

@Agent("dhl")
class DHLAgent:

    @Timed(300)
    def update(self):
        ret = []
        print("Hi, I'm the DHL agent and I'll check these ids:");
        for sender, ident in zoe.state.Stuff.all(CATEGORY):
            print("Checking", ident, "from", sender)
            new = "\n".join(self.track(ident))
            stored = zoe.state.Stuff(sender, CATEGORY, ident)
            current = stored.text()
            if current != new:
                print("New events!")
                stored.write(new)
                m = zoe.MessageBuilder({"dst":"broadcast", "tag":"send", "msg":"Nuevos eventos en tu envío %s:\n%s" % (ident, new), "to":sender})
                ret.append(m)
        return ret

    @Message(tags = ["track"])
    def tracknew(self, sender, identifier):
        print("I have to track ID", identifier)
        stuff = zoe.state.Stuff(sender, CATEGORY, identifier)
        stuff.write("")

    @Message(tags = ["untrack"])
    def untrack(self, sender, identifier):
        print("I have to stop tracking track ID", identifier)
        stuff = zoe.state.Stuff(sender, CATEGORY, identifier)
        stuff.remove()

    def track(self, ident):
        request="""<?xml version="1.0" encoding="UTF-8"?>
<req:KnownTrackingRequest xmlns:req="http://www.dhl.com" 
						xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
						xsi:schemaLocation="http://www.dhl.com
						TrackingRequestKnown.xsd">
	<Request>
		<ServiceHeader>
			<MessageTime>2002-06-25T11:28:56-08:00</MessageTime>
			<MessageReference>1234567890123456789012345678</MessageReference>
            		<SiteID>DServiceVal</SiteID>
            		<Password>testServVal</Password>
		</ServiceHeader>
	</Request>
	<LanguageCode>en</LanguageCode>
	<AWBNumber>%s</AWBNumber>
	<LevelOfDetails>ALL_CHECK_POINTS</LevelOfDetails>
	<PiecesEnabled>S</PiecesEnabled> 
</req:KnownTrackingRequest>""" % (ident)
        conn = http.client.HTTPConnection("xmlpitest-ea.dhl.com", 80)
        conn.request("POST", "/XMLShippingServlet", request)
        response = conn.getresponse()
        if int(response.status) != 200:
            print("Can't track id", ident)
            return

        data = response.read().decode("UTF-8")
        dom = xml.dom.minidom.parseString(data)
        dom = dom.childNodes[0]
        events = dom.getElementsByTagName("AWBInfo")[0].getElementsByTagName("ShipmentInfo")[0].getElementsByTagName("ShipmentEvent")
        allevents = []
        for event in events:
            date = event.getElementsByTagName("Date")[0].childNodes[0].data
            time = event.getElementsByTagName("Time")[0].childNodes[0].data
            what = event.getElementsByTagName("ServiceEvent")[0].getElementsByTagName("Description")[0].childNodes[0].data
            where = event.getElementsByTagName("ServiceArea")[0].getElementsByTagName("Description")[0].childNodes[0].data 
            txt = "%s %s %s : %s" % (date, time, where, what)
            allevents.append(txt)
        return allevents

