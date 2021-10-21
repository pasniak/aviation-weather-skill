Feature: metar
  Scenario: metar for an airport by FAA abbreviation spelled
    Given an english speaking user
    When the user says "metar kjfk"
    Then "aviation-weather-skill" reply should contain "temperature"
