
PLAINTEXT_FLAGS_dummy = [
    ("SQLI", "FLAG{I_am_scared_of_injection}", "Extract the hidden data via SQL injection"),
    ("SQLI_ADV", "FLAG{Try_this_injection_and_you_will_be_scared_too}", "Chain UNION SELECT payloads against confidential contracts"),
    ("SQLI_BLIND", "FLAG{If_I_am_leaving_a_footprint_its_not_mistake}", "Use boolean/blind techniques to exfiltrate secret data"),
    ("XSS", "FLAG{Try_this_one}", "Pop an alert and steal the flag with stored XSS"),
    ("CSRF", "FLAG{Hello_from_the_other_side}", "Forge a state-changing request to grab this flag"),
    ("STEG", "FLAG{Still_trying_dummy_flags}", "Bonus stego puzzle hidden in the site chrome."),
]

