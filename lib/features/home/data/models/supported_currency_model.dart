import 'package:currency_converter_app/features/home/domain/entity/supported_currency.dart';

class SupportedCurrencyModel extends SupportedCurrency {
  SupportedCurrencyModel({
    required this.currencyCode,
    required this.currencyName,
    required this.countryCode,
    required this.status,
    required this.icon,
  }) : super(
         currencyCode: currencyCode,
         currencyName: currencyName,
         countryCode: currencyCode,
         status: status,
         icon: icon,
       );

  final String currencyCode;
  final String currencyName;
  final String countryCode;
  final String status;
  final String icon;

  factory SupportedCurrencyModel.fromMap(Map<String, dynamic> json) =>
      SupportedCurrencyModel(
        currencyCode: json["currency_code"],
        currencyName: json["currency_name"],
        countryCode: json["country_code"],
        status: json["status"],
        icon: json["icon"],
      );
}
