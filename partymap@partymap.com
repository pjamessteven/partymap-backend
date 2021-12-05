import requests
import json
import time
from random import randint

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:91.0) Gecko/20100101 Firefox/91.0",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
    "Content-Type": "application/x-www-form-urlencoded",
    "X-FB-Friendly-Name": "SearchCometResultsPaginatedResultsQuery",
    "X-FB-LSD": "AVpXUXcBmW8",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}

cursor = "null"  # start with null curosr
i = 0
events = []

while i < 10000:
    time.sleep(randint(1, 20))
    data = (
        "av=0&__user=0&__a=1&__dyn=7xeUmwlEnwn8K2WnFw9-2i5U4e0yoW3q32360CEbo19oe8hw2nVE4W0om782Cw868wlU-cw5MKdwl8G0Boy1PwBgao6C0Mo5W3S1lwlE-Uqw8y4UaEW0D888brwKwHw8Xwn82FBwxw8W0BFobodEGdw46w&__csr=hIYJcPOABGKhpER4FJy4tzWDBzVka-USUx4Kcxi7pbxd2K8zE98kyudx22Wi7qDUaEkAK2a3GiUuwqEjg03ACg1280EW1HhoOq1kxN4wJG0cow4qw7ow2L80uuw0mtm&__req=5y&__hs=18892.HYP%3Acomet_loggedout_pkg.2.0.0.0.1&dpr=1&__ccg=EXCELLENT&__rev=1004434914&__s=0upeb6%3Afoejv4%3A8icuc1&__hsi=7010675960000339317-0&__comet_req=1&lsd=AVpXUXcBmW8&jazoest=2941&__spin_r=1004434914&__spin_b=trunk&__spin_t=1632300196&fb_api_caller_class=RelayModern&fb_api_req_friendly_name=SearchCometResultsInitialResultsQuery&variables=%7B%22count%22%3A5%2C%22allow_streaming%22%3Afalse%2C%22args%22%3A%7B%22callsite%22%3A%22comet%3Aevents_search%22%2C%22config%22%3A%7B%22bootstrap_config%22%3Anull%2C%22exact_match%22%3Afalse%2C%22high_confidence_config%22%3Anull%2C%22intercept_config%22%3Anull%2C%22sts_disambiguation%22%3Anull%2C%22watch_config%22%3Anull%7D%2C%22context%22%3A%7B%22bsid%22%3A%2248a7485f-fe92-48ed-966c-86555b8e2d64%22%2C%22tsid%22%3Anull%7D%2C%22experience%22%3A%7B%22encoded_server_defined_params%22%3A%22AbrQ9KopLfqYT7heXVVCxznkZYxRr9hU1JA4cdLbJhjgs56yyeHW3e833A9dGP1WlEHOyagjWyFL9Y79gw-Ko1iVuJCILVkpVsHkmSbBFb3SEA%22%2C%22fbid%22%3Anull%2C%22type%22%3A%22SERVER_DEFINED%22%7D%2C%22filters%22%3A%5B%22%7B%5C%22name%5C%22%3A%5C%22filter_events_category%5C%22%2C%5C%22args%5C%22%3A%5C%22183019258855149%5C%22%7D%22%5D%2C%22text%22%3A%22Party%22%7D%2C%22cursor%22%3A"
        + cursor
        + "%2C%22feedbackSource%22%3A23%2C%22fetch_filters%22%3Atrue%2C%22renderLocation%22%3Anull%2C%22scale%22%3A1%2C%22stream_initial_count%22%3A0%7D&server_timestamps=true&doc_id=4882952861734198"
    )
    """
    data = 'av=0&__user=0&__a=1&__dyn=7xeUmwlEnwn8K2WnFw9-2i5U4e0yoW3q32360CEbo19oe8hw2nVE4W0om782Cw868wlU-cw5MKdwl8G0Boy1PwBgao6C0Mo5W3S1lwlE-Uqw8y4UaEW0D888brwKwHw8Xwn82FBwxw8W0BFobodEGdw46w&__csr=hIYJcPOABGKhpER4FJy4tzWDBzVka-USUx4Kcxi7pbxd2K8zE98kyudx22Wi7qDUaEkAK2a3GiUuwqEjg03ACg1280EW1HhoOq1kxN4wJG0cow4qw7ow2L80uuw0mtm&__req=d&__hs=18892.HYP%3Acomet_loggedout_pkg.2.0.0.0.1&dpr=1&__ccg=EXCELLENT&__rev=1004434914&__s=p8mhyp%3Afoejv4%3A14rr1k&__hsi=7010695162467237094-0&__comet_req=1&lsd=AVpXUXcBCS0&jazoest=2887&__spin_r=1004434914&__spin_b=trunk&__spin_t=1632304667&fb_api_caller_class=RelayModern&fb_api_req_friendly_name=SearchCometResultsPaginatedResultsQuery&variables=%7B%22UFI2CommentsProvider_commentsKey%22%3A%22SearchCometResultsInitialResultsQuery%22%2C%22allow_streaming%22%3Afalse%2C%22args%22%3A%7B%22callsite%22%3A%22comet%3Aevents_search%22%2C%22config%22%3A%7B%22bootstrap_config%22%3Anull%2C%22exact_match%22%3Afalse%2C%22high_confidence_config%22%3Anull%2C%22intercept_config%22%3Anull%2C%22sts_disambiguation%22%3Anull%2C%22watch_config%22%3Anull%7D%2C%22context%22%3A%7B%22bsid%22%3A%22a4cd5b01-b450-48d4-8c1f-d4dedb42ee65%22%2C%22tsid%22%3Anull%7D%2C%22experience%22%3A%7B%22encoded_server_defined_params%22%3A%22AbrQ9KopLfqYT7heXVVCxznkZYxRr9hU1JA4cdLbJhjgs56yyeHW3e833A9dGP1WlEHOyagjWyFL9Y79gw-Ko1iVuJCILVkpVsHkmSbBFb3SEA%22%2C%22fbid%22%3Anull%2C%22type%22%3A%22SERVER_DEFINED%22%7D%2C%22filters%22%3A%5B%22%7B%5C%22name%5C%22%3A%5C%22filter_events_category%5C%22%2C%5C%22args%5C%22%3A%5C%22183019258855149%5C%22%7D%22%5D%2C%22text%22%3A%22Party%22%7D%2C%22count%22%3A5%2C%22cursor%22%3A%22AboeJ03UnqkymJaBqr6acV59AoxuxNobLADStK3QEocemwYbKabVg6YH2O2983DNK7XU9zNKNpZeo57OWsWiuEmCfAIpBhi15JSG495ypTDnrthMJ7qP_JLUzo58kLCEmRpRaRANBZac0P9ihh5Tsy02zFuDdVoEWv5g34gNgrO4ED3Q1PeOi_NddWD0fmbWvdANC2lSzNp3mgk3zhs3xRdOFA_GiOxkVovFI3zEqzr1_hzqs_xoH4tvvYKQ6SsqG9-pSg-roAnE5XyZYOLFhWe8bERohaltBL2fD7hb7l79U46Rsm4HFYbEm17W4R6kr1bCaNkduoWVtnFHxe8jas5gQ_mQVzgm6l1foh2osvLEbv08AEL4yAFHWrWVf-nAC3KpxscwPSrX8Hse7gLhkhbmqchhERUjcpZJiCFdNEF9oGnZW_X_xTfmjv8qPbHbtDZQasxxtQBvpF9es3x2NIzw3vxEBrLJ96nU1wMZwsCRE47lnpVpuPmnZVknNLoL0RmMLi0a4Vk512KGMfMhcHGFr60nH44IDAzA6EcEVaJSMnc6WJ6I0krYL6DCrN1GGW3QPBZuy7GAlZ9Bg9WGbYbiOfgylGfA1_cqBFUubWhzRqizTNtcnx4Z3QF1N4drU3HPEyseTDwQUKhXPjnoz-_qmBfv9wfK5TswPbELzaIfla03WifEueVl2NrKz-K1FcjLqUiYlK0ySAAw6lII6aveGu7YrUb7aHZhse2RRuQqNhG9SpIKF-vDdpW9CEQxhmMWylVGBEQP54z0ogb31myHkQklWxFC0dwVzNO41tnvDdFDZ9IswtXxy5paN1i5NyfyAQHzZ87zyjxXc3OndJrkUL2Q5HYWbxtXTUMs3RO2YBPTFJHCPpJefSdukRDO6zB_MOTSf7iUsBaOwNvF0CJPosP4hK6tQYVmiM7O-XyjI6VCmFqIXlmTNixOjFhvi3GVy92yPZVV8_cth1VHcQLFaEE75Oy43bj4mUT8Wehx9D5yOVIvevO2qv4CxpIjpdcDEGgSWVi-fi_RQVUFpye-d1wbo4e36GEyohN2dXjJZwFoUaSwTe0sukCK0uGOMnBNk10ZmPc-ugkFDrWlwCRZrZFIt7vYxW-3Y53Cw4MNZvKpco84gpimk_qSS_vJNGgXRracKsHNqQbb_EZBrDHI2_SRxY57G9G-NlRgWSQZRAJgW4yaIOisGU_cSD3hw9eQfYOTjeA87XX5gQ-d3CNJerV4W1OZnlRBlOL3jAKy8RIrndccTur61olitIrALXu69V3cWmK_2AFG8bv82IGkuxpGOc3NC93m7rfCXNIVmEEl3e1sRyj2WhgvQY9ZjjFB8cotoWtUaC95BYAsHmSKJE0Bb7gtDvaft3GzQI3-Y8Ct1Y_vPYsJOh5oIpSOJDFP6BsSYNwZev3Sif9q0LobjQCdDA9-ctvmvF-CE7S4yM8Ci5HcXns3voMgCod1Q_ESR3nIgfe0k4wuSUZR3KugunkJnV4k94gPb3KTXNZniFKmXXmIpytt2HmsdXacRVcdzP4YbuacVQFBAVU1w3MJOh5Xw_5jxh6U-YJyjOfZa1rmJJDSlM5y7uk_0AW42Ijl0xeIMk4i9WDHyhkzw2s4rL3UYDbAylGs7rcgC7FSdulCGnBv_KvgSUZeX7htaNfDp_-ifyjCevAbWTyRy_oiRF3UpwcjNLd9kRl0aHxgbUiUjWNMqlTSvGWd5OTuOFqKZ6pQnC1unIoVn8x4mq3erBWHcyUOhKeqsUKSkPrNT36YYwHH5wlCYM03RVa33CzIru6dD7Q3MdIvL3WejeITzpqOVS_l_G5HsS-7L1GCpALtqpYTDa5kgmUHdcR2DjbA-UipgqFibqggR2UccQAo%22%2C%22displayCommentsContextEnableComment%22%3Afalse%2C%22displayCommentsContextIsAdPreview%22%3Afalse%2C%22displayCommentsContextIsAggregatedShare%22%3Afalse%2C%22displayCommentsContextIsStorySet%22%3Afalse%2C%22displayCommentsFeedbackContext%22%3Anull%2C%22feedLocation%22%3A%22SEARCH%22%2C%22feedbackSource%22%3A23%2C%22fetch_filters%22%3Atrue%2C%22focusCommentID%22%3Anull%2C%22locale%22%3Anull%2C%22privacySelectorRenderLocation%22%3A%22COMET_STREAM%22%2C%22renderLocation%22%3Anull%2C%22scale%22%3A1%2C%22stream_initial_count%22%3A0%2C%22useDefaultActor%22%3Afalse%7D&server_timestamps=true&doc_id=4332129683532231'
        """

    r = requests.post(
        "https://www.facebook.com/api/graphql/", headers=headers, data=data
    )
    data = r.json()

    if data.get("data", {}).get("serpResponse", {}).get("results", {}).get("edges"):

        for item in data["data"]["serpResponse"]["results"]["edges"]:
            events.append(
                {
                    "name": item["relay_rendering_strategy"]["view_model"]["profile"][
                        "name"
                    ],
                    "id": item["relay_rendering_strategy"]["view_model"]["profile"][
                        "id"
                    ],
                    "url": item["relay_rendering_strategy"]["view_model"]["profile"][
                        "url"
                    ],
                }
            )

        cursor = (
            "%22"
            + r.json()["data"]["serpResponse"]["results"]["page_info"]["end_cursor"]
            + "%22"
        )
        print("round", i)
        i += 1

    else:
        break

# Serializing json
json_object = json.dumps(events, indent=4)

# Writing to sample.json
with open("sample.json", "w") as outfile:
    outfile.write(json_object)
